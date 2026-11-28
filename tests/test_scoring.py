"""Unit tests for the hit@5 referee. Written before the code (test-driven)."""

import pytest

from scoreboard.scoring import credit_acceptable, hit_at_k, is_hit, mean_recall_at_k, mrr, ndcg_at_k, recall_at_k


# --- is_hit: one question ---------------------------------------------------

def test_right_answer_first_is_a_hit():
    assert is_hit(["KB0001", "KB0002", "KB0003"], "KB0001") is True


def test_right_answer_fifth_is_still_a_hit():
    assert is_hit(["KB0009", "KB0008", "KB0007", "KB0006", "KB0001"], "KB0001") is True


def test_right_answer_sixth_is_a_miss():
    ranked = ["KB0009", "KB0008", "KB0007", "KB0006", "KB0005", "KB0001"]
    assert is_hit(ranked, "KB0001") is False


def test_right_answer_missing_is_a_miss():
    assert is_hit(["KB0009", "KB0008"], "KB0001") is False


def test_no_results_is_a_miss():
    assert is_hit([], "KB0001") is False


def test_fewer_than_five_results_still_counts():
    assert is_hit(["KB0002", "KB0001"], "KB0001") is True


def test_k_can_be_changed():
    ranked = ["KB0009", "KB0001"]
    assert is_hit(ranked, "KB0001", k=1) is False
    assert is_hit(ranked, "KB0001", k=2) is True


# --- hit_at_k: the whole exam ------------------------------------------------

ANSWERS = {"Q01": "KB0001", "Q02": "KB0002", "Q03": "KB0003", "Q04": "KB0004"}


def test_all_hits_scores_one():
    results = {q: [a] for q, a in ANSWERS.items()}
    assert hit_at_k(results, ANSWERS) == 1.0


def test_no_hits_scores_zero():
    results = {q: ["KB0999"] for q in ANSWERS}
    assert hit_at_k(results, ANSWERS) == 0.0


def test_partial_score_is_the_share_of_hits():
    results = {
        "Q01": ["KB0001"],                      # hit
        "Q02": ["KB0999", "KB0002"],            # hit at rank 2
        "Q03": ["KB0999"],                      # miss
        "Q04": ["KB0999"] * 5 + ["KB0004"],     # rank 6: miss
    }
    assert hit_at_k(results, ANSWERS) == 0.5


def test_question_missing_from_results_counts_as_a_miss():
    results = {"Q01": ["KB0001"], "Q02": ["KB0002"], "Q03": ["KB0003"]}  # no Q04
    assert hit_at_k(results, ANSWERS) == 0.75


def test_empty_answer_key_is_an_error():
    with pytest.raises(ValueError):
        hit_at_k({}, {})


# --- mrr: rewards ranking the right answer higher ------------------------------

def test_mrr_right_answer_first_scores_one():
    assert mrr({"Q01": ["KB0001", "KB0009"]}, {"Q01": "KB0001"}) == pytest.approx(1.0)


def test_mrr_right_answer_second_scores_a_half():
    assert mrr({"Q01": ["KB0009", "KB0001"]}, {"Q01": "KB0001"}) == pytest.approx(0.5)


def test_mrr_right_answer_fifth_scores_a_fifth():
    ranked = ["KB0009", "KB0008", "KB0007", "KB0006", "KB0001"]
    assert mrr({"Q01": ranked}, {"Q01": "KB0001"}) == pytest.approx(0.2)


def test_mrr_right_answer_missing_scores_zero():
    assert mrr({"Q01": ["KB0009", "KB0008"]}, {"Q01": "KB0001"}) == pytest.approx(0.0)


def test_mrr_averages_over_questions():
    results = {
        "Q01": ["KB0001"],                 # rank 1 -> 1.0
        "Q02": ["KB0999", "KB0002"],       # rank 2 -> 0.5
        "Q03": ["KB0999"],                 # missing -> 0.0
        "Q04": ["KB0999"] * 3 + ["KB0004"],  # rank 4 -> 0.25
    }
    assert mrr(results, ANSWERS) == pytest.approx((1 + 0.5 + 0 + 0.25) / 4)


def test_mrr_question_missing_from_results_scores_zero():
    results = {"Q01": ["KB0001"], "Q02": ["KB0002"], "Q03": ["KB0003"]}  # no Q04
    assert mrr(results, ANSWERS) == pytest.approx(0.75)


def test_mrr_empty_answer_key_is_an_error():
    with pytest.raises(ValueError):
        mrr({}, {})


# --- credit_acceptable: lenient marking ------------------------------------------

QUESTIONS = [
    {"id": "Q01", "answer_article_id": "KB0001", "also_relevant": ["KB0009"]},
    {"id": "Q02", "answer_article_id": "KB0002"},
]


def test_acceptable_twin_counts_as_the_answer_at_its_position():
    results = {"Q01": ["KB0005", "KB0009", "KB0007"], "Q02": ["KB0002"]}
    credited = credit_acceptable(results, QUESTIONS)
    assert credited["Q01"] == ["KB0005", "KB0001", "KB0007"]
    assert mrr(credited, {"Q01": "KB0001"}) == pytest.approx(0.5)


def test_answer_and_twin_both_present_keeps_the_better_rank():
    results = {"Q01": ["KB0009", "KB0001"], "Q02": ["KB0002"]}
    assert credit_acceptable(results, QUESTIONS)["Q01"] == ["KB0001"]


def test_questions_without_twins_are_unchanged():
    results = {"Q01": ["KB0005"], "Q02": ["KB0008", "KB0002"]}
    assert credit_acceptable(results, QUESTIONS)["Q02"] == ["KB0008", "KB0002"]


def test_strict_marking_ignores_twins():
    results = {"Q01": ["KB0009"], "Q02": ["KB0002"]}
    answers = {"Q01": "KB0001", "Q02": "KB0002"}
    assert hit_at_k(results, answers) == 0.5
    assert hit_at_k(credit_acceptable(results, QUESTIONS), answers) == 1.0


# --- recall@k ---------------------------------------------------------------------

def test_recall_one_relevant_found_or_not():
    assert recall_at_k(["KB0001", "KB0002"], {"KB0001"}) == 1.0
    assert recall_at_k(["KB0003", "KB0002"], {"KB0001"}) == 0.0


def test_recall_counts_the_share_of_relevant_articles_found():
    ranked = ["KB0001", "KB0009", "KB0002", "KB0008", "KB0007"]
    assert recall_at_k(ranked, {"KB0001", "KB0002", "KB0003"}) == pytest.approx(2 / 3)


def test_recall_ignores_positions_past_k():
    assert recall_at_k(["KB0009"] * 5 + ["KB0001"], {"KB0001"}, k=5) == 0.0


# --- nDCG@k (boss fight #6) -------------------------------------------------------

def test_ndcg_one_relevant_at_rank_1_is_perfect():
    assert ndcg_at_k(["KB0001", "KB0002"], {"KB0001"}) == pytest.approx(1.0)


def test_ndcg_one_relevant_at_rank_2():
    # 1 / log2(3) = 0.6309
    assert ndcg_at_k(["KB0009", "KB0001"], {"KB0001"}) == pytest.approx(0.6309, abs=1e-4)


def test_ndcg_one_relevant_at_rank_3_is_a_half():
    assert ndcg_at_k(["KB0009", "KB0008", "KB0001"], {"KB0001"}) == pytest.approx(0.5)


def test_ndcg_missing_scores_zero():
    assert ndcg_at_k(["KB0009", "KB0008"], {"KB0001"}) == 0.0


def test_ndcg_ignores_positions_past_k():
    assert ndcg_at_k(["KB0009"] * 10 + ["KB0001"], {"KB0001"}, k=10) == 0.0


def test_ndcg_two_relevant_at_the_top_is_perfect():
    assert ndcg_at_k(["KB0002", "KB0001", "KB0009"], {"KB0001", "KB0002"}) == pytest.approx(1.0)


def test_ndcg_two_relevant_at_1_and_3():
    # (1 + 1/log2(4)) / (1 + 1/log2(3)) = 1.5 / 1.6309 = 0.9197
    assert ndcg_at_k(["KB0001", "KB0009", "KB0002"], {"KB0001", "KB0002"}) == pytest.approx(0.9197, abs=1e-4)


def test_ndcg_empty_ranking_scores_zero():
    assert ndcg_at_k([], {"KB0001"}) == 0.0


def test_ndcg_empty_relevant_set_is_an_error():
    with pytest.raises(ValueError):
        ndcg_at_k(["KB0001"], set())


# --- averages over an exam ----------------------------------------------------------

def test_mean_recall_uses_answer_and_also_relevant():
    questions = [{"id": "Q01", "answer_article_id": "KB0001", "also_relevant": ["KB0002"]}]
    assert mean_recall_at_k({"Q01": ["KB0002", "KB0009"]}, questions) == pytest.approx(0.5)
