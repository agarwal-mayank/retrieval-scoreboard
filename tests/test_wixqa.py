"""Tests for the WixQA loader and the Haiku reranker's plumbing (no network)."""

from types import SimpleNamespace

from scoreboard.rerank import HaikuReranker, build_prompt, estimate_haiku_cost
from scoreboard.report import summarize
from scoreboard.wixqa import first_line, to_articles, to_questions

CORPUS = [
    {"id": "a1", "url": "u", "contents": "\n  Add a domain  \nGo to settings.", "article_type": "article"},
    {"id": "a2", "url": "u", "contents": "x" * 300, "article_type": "known_issue"},
]
QUESTION_ROWS = [
    {"question": "How do I add a domain?", "answer": "...", "article_ids": ["a1"]},
    {"question": "Two answers?", "answer": "...", "article_ids": ["a2", "a1", "a3"]},
]


def test_title_is_the_first_non_empty_line_capped_at_120_chars():
    articles = to_articles(CORPUS)
    assert articles[0]["title"] == "Add a domain"
    assert len(articles[1]["title"]) == 120
    assert first_line("") == ""


def test_article_keeps_category_and_full_body():
    a = to_articles(CORPUS)[0]
    assert a["category"] == "article" and a["body"] == CORPUS[0]["contents"]


def test_questions_get_ids_type_answer_and_also_relevant():
    qs = to_questions(QUESTION_ROWS, "E", "expert")
    assert [q["id"] for q in qs] == ["E001", "E002"]
    assert qs[0]["answer_article_id"] == "a1" and qs[0]["also_relevant"] == []
    assert qs[1]["answer_article_id"] == "a2" and qs[1]["also_relevant"] == ["a1", "a3"]
    assert all(q["type"] == "expert" for q in qs)


def test_report_handles_new_question_types_with_lenient_numbers():
    qs = to_questions(QUESTION_ROWS, "E", "expert") + to_questions(QUESTION_ROWS[:1], "S", "simulated")
    results = {"E001": ["a1"], "E002": ["a1"], "S001": ["a9"]}
    s = summarize(results, qs, "m", exam="wixqa")
    assert list(s["by_type"]) == ["expert", "simulated"]
    assert s["by_type"]["expert"]["mrr"] == 0.5  # E002 strict-misses
    assert s["by_type_lenient"]["expert"]["mrr"] == 1.0  # a1 is also relevant for E002
    assert s["by_type_lenient"]["simulated"]["mrr"] == 0.0


def test_prompt_trims_bodies_to_max_words():
    prompt = build_prompt("q", [{"title": "T", "body": "one two three four"}], max_words=2)
    assert "one two" in prompt and "three" not in prompt


class FakeClient:
    def __init__(self, text):
        self.calls = []
        reply = SimpleNamespace(
            content=[SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text=text)],
            usage=SimpleNamespace(input_tokens=100, output_tokens=7),
        )
        self.messages = SimpleNamespace(create=lambda **kw: (self.calls.append(kw), reply)[1])


CANDS = [{"title": "A", "body": "a"}, {"title": "B", "body": "b"}, {"title": "C", "body": "c"}]


def test_haiku_reranker_reorders_and_counts_tokens():
    client = FakeClient("3, 1, 2")
    r = HaikuReranker(client=client)
    assert [a["title"] for a in r.rerank("q", CANDS)] == ["C", "A", "B"]
    assert (r.input_tokens, r.output_tokens, r.fallbacks) == (100, 7, 0)
    call = client.calls[0]
    assert call["model"] == "claude-haiku-5-5" and call["output_config"] == {"effort": "low"}
    assert not {"temperature", "top_p", "top_k"} & set(call)


def test_haiku_reranker_falls_back_on_unreadable_reply():
    r = HaikuReranker(client=FakeClient("no idea"))
    assert r.rerank("q", CANDS) == CANDS and r.fallbacks == 1


def test_cost_estimate_uses_chars_over_four_times_1_3():
    tokens, cost = estimate_haiku_cost(["x" * 4000], output_tokens_per_call=0)
    assert tokens == 1300 and abs(cost - 1300 / 1e6 * 0.10) < 1e-12


def test_spend_ledger_accumulates_and_guard_stops_over_budget(tmp_path):
    import pytest

    from scoreboard.rerank import check_haiku_budget, record_spend, spent_so_far

    ledger = str(tmp_path / "spend.json")
    assert spent_so_far(ledger) == 0.0
    record_spend(0.25, ledger)
    record_spend(0.5, ledger)
    assert spent_so_far(ledger) == 0.75
    check_haiku_budget(["x" * 400], ledger=ledger)  # tiny: fine
    with pytest.raises(SystemExit):
        check_haiku_budget(["x" * 4_000_000], ledger=ledger, budget=0.8)  # over budget
