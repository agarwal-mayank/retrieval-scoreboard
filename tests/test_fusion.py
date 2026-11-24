"""Unit tests for Reciprocal Rank Fusion. Written before the code."""

import pytest

from scoreboard.fusion import rrf


def test_a_single_ranking_keeps_its_order():
    assert rrf([["KB0001", "KB0002", "KB0003"]]) == ["KB0001", "KB0002", "KB0003"]


def test_an_article_both_methods_like_rises_to_the_top():
    # KB0002: 1/62 + 1/61 beats KB0001's 1/61 alone
    assert rrf([["KB0001", "KB0002"], ["KB0002", "KB0003"]]) == ["KB0002", "KB0001", "KB0003"]


def test_the_docstring_example():
    assert rrf([["A", "B"], ["B", "C"]]) == ["B", "A", "C"]


def test_every_article_from_every_ranking_is_kept():
    merged = rrf([["KB0001", "KB0002"], ["KB0003", "KB0004"]])
    assert sorted(merged) == ["KB0001", "KB0002", "KB0003", "KB0004"]


def test_ties_keep_the_order_first_seen():
    # Both are #1 in their own list, so equal scores: the first list's comes first
    assert rrf([["KB0001"], ["KB0009"]]) == ["KB0001", "KB0009"]


def test_k_controls_how_much_rank_matters():
    # KB0009 is 4th in both lists; KB0001 is 1st in one list only.
    rankings = [["KB0001", "KB0002", "KB0003", "KB0009"], ["KB0005", "KB0006", "KB0007", "KB0009"]]
    assert rrf(rankings, k=1)[0] == "KB0001"   # tiny k: 1/2 = 0.5 beats 1/5 + 1/5 = 0.4
    assert rrf(rankings, k=60)[0] == "KB0009"  # k=60: 2/64 beats 1/61, so agreement wins


def test_no_rankings_gives_an_empty_list():
    assert rrf([]) == []


# --- weighted fusion --------------------------------------------------------------


def test_equal_weights_match_no_weights():
    rankings = [["A", "B"], ["B", "C"]]
    assert rrf(rankings, weights=[1, 1]) == rrf(rankings)


def test_a_heavier_ranking_wins_a_disagreement():
    # Both lists put a different article first; the 70% list should win.
    assert rrf([["A"], ["B"]], weights=[0.7, 0.3]) == ["A", "B"]
    assert rrf([["A"], ["B"]], weights=[0.3, 0.7]) == ["B", "A"]


def test_agreement_can_still_beat_a_heavier_first_place():
    # C is 2nd in both lists: 0.7/62 + 0.3/62 beats A's 0.7/61 alone
    assert rrf([["A", "C"], ["B", "C"]], weights=[0.7, 0.3])[0] == "C"


def test_one_weight_per_ranking_is_required():
    with pytest.raises(ValueError):
        rrf([["A"], ["B"]], weights=[1.0])
