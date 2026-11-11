"""Unit tests for the hit@5 referee. Written before the code (test-driven)."""

import pytest

from scoreboard.scoring import hit_at_k, is_hit


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
