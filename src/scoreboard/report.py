"""Shared scoreboard report: the same metrics and printout for every search method."""

import json
from collections import defaultdict
from pathlib import Path

from scoreboard.scoring import hit_at_k, is_hit, mrr

TYPES = ["easy", "paraphrase", "near-twin", "messy"]


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def metrics(results, key):
    """hit@5, hit@1 and MRR for one answer key (all questions, or one type)."""
    return {
        "questions": len(key),
        "hit@5": hit_at_k(results, key, k=5),
        "hit@1": hit_at_k(results, key, k=1),
        "mrr": mrr(results, key),
    }


def summarize(results, questions, method, exam="v1"):
    answers = {q["id"]: q["answer_article_id"] for q in questions}
    by_type = defaultdict(dict)
    for q in questions:
        by_type[q["type"]][q["id"]] = q["answer_article_id"]
    return {
        "method": method,
        "exam": exam,
        "overall": metrics(results, answers),
        "by_type": {t: metrics(results, by_type[t]) for t in TYPES},
    }


def print_report(summary, results, questions, titles):
    print(f"\n{summary['method']}, exam {summary['exam']}\n")
    print(f"  {'':<11} {'n':>3}  {'hit@5':>6}  {'hit@1':>6}  {'MRR':>5}")
    rows = [("overall", summary["overall"])] + list(summary["by_type"].items())
    for label, m in rows:
        print(f"  {label:<11} {m['questions']:>3}  {m['hit@5']:6.1%}  {m['hit@1']:6.1%}  {m['mrr']:5.3f}")

    both = [q for q in questions if q.get("also_relevant")]
    if both:
        found = sum(
            is_hit(results[q["id"]], q["answer_article_id"])
            and all(a in results[q["id"]] for a in q["also_relevant"])
            for q in both
        )
        print(f"\n  two-intent questions with both articles in the top 5: {found} of {len(both)}")

    misses = [q for q in questions if not is_hit(results[q["id"]], q["answer_article_id"])]
    print(f"\nMisses from the top 5 ({len(misses)}):")
    for q in misses:
        print(f"  {q['id']} [{q['type']}] {q['question']}")
        print(f"      wanted {q['answer_article_id']} {titles[q['answer_article_id']]}")
        print(f"      got #1 {results[q['id']][0]} {titles[results[q['id']][0]]}")

    not_first = [
        q for q in questions
        if is_hit(results[q["id"]], q["answer_article_id"]) and results[q["id"]][0] != q["answer_article_id"]
    ]
    print(f"\nIn the top 5 but not #1 ({len(not_first)}):")
    for q in not_first:
        rank = results[q["id"]].index(q["answer_article_id"]) + 1
        print(f"  {q['id']} [{q['type']}] rank {rank}: {q['question']}")
        print(f"      #1 was {results[q['id']][0]} {titles[results[q['id']][0]]}")


def save(summary, results, name):
    out = Path("runs/results")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}_{summary['exam']}.json"
    path.write_text(json.dumps({"summary": summary, "results": results}, indent=2) + "\n", encoding="utf-8")
    return path
