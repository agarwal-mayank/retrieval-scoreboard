"""Unit tests for cosine similarity and top-k ranking. Written before the code."""

import pytest

from scoreboard.vector_search import cosine_similarity, top_k

# Decimals can come out as 0.9999999999 instead of 1.0, so floats are compared
# with pytest.approx ("equal, allowing a tiny rounding difference").


# --- cosine_similarity ---------------------------------------------------------

def test_same_vector_scores_one():
    assert cosine_similarity([3, 4], [3, 4]) == pytest.approx(1.0)


def test_same_direction_longer_arrow_still_scores_one():
    assert cosine_similarity([3, 4], [6, 8]) == pytest.approx(1.0)


def test_right_angles_score_zero():
    assert cosine_similarity([3, 4], [4, -3]) == pytest.approx(0.0)


def test_opposite_directions_score_minus_one():
    assert cosine_similarity([1, 2], [-1, -2]) == pytest.approx(-1.0)


def test_in_between_angle():
    # (1, 0) vs (1, 1): dot = 1, lengths 1 and sqrt(2) -> 1 / sqrt(2), about 0.707
    assert cosine_similarity([1, 0], [1, 1]) == pytest.approx(0.7071, abs=1e-4)


def test_works_with_many_numbers():
    a = [0.1] * 768
    b = [0.2] * 768
    assert cosine_similarity(a, b) == pytest.approx(1.0)


def test_zero_vector_is_an_error():
    with pytest.raises(ValueError):
        cosine_similarity([0, 0], [1, 1])


# --- top_k ----------------------------------------------------------------------

ARTICLES = {
    "KB0001": [1, 0],    # points right
    "KB0002": [0, 1],    # points up
    "KB0003": [1, 1],    # diagonal
    "KB0004": [-1, 0],   # points left
}


def test_best_match_comes_first():
    assert top_k([1, 0], ARTICLES, k=1) == ["KB0001"]


def test_returns_k_ids_best_first():
    assert top_k([1, 0.1], ARTICLES, k=3) == ["KB0001", "KB0003", "KB0002"]


def test_fewer_articles_than_k_returns_them_all():
    assert top_k([1, 0], ARTICLES, k=10) == ["KB0001", "KB0003", "KB0002", "KB0004"]


def test_default_k_is_five():
    many = {f"KB{i:04d}": [1, i] for i in range(1, 9)}
    assert len(top_k([1, 0], many)) == 5
