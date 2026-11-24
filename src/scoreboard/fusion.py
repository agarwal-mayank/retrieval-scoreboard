"""Hybrid search: merge several methods' rankings into one."""


def rrf(rankings: list[list[str]], k: int = 60, weights: list[float] | None = None) -> list[str]:
    """Reciprocal Rank Fusion: merge rankings into one list, best first.

    Each ranking votes for its articles: an article at position r (counting
    from 1) gets 1 / (k + r) from that ranking. An article's score is the sum
    of its votes from every ranking it appears in. Articles both methods like
    rise to the top; k (60 is the usual value) stops any single #1 dominating.

    Weighted fusion: weights (one per ranking, e.g. [0.7, 0.3]) multiply each
    ranking's votes, so a stronger method counts for more. No weights = equal.

    Ties keep the order in which articles were first seen.
    Example: rrf([["A", "B"], ["B", "C"]]) -> ["B", "A", "C"]
    """
    if weights is None:
        weights = [1.0] * len(rankings)
    if len(weights) != len(rankings):
        raise ValueError("Give one weight per ranking")
    scores = {}
    for ranking, weight in zip(rankings, weights):
        for position, article_id in enumerate(ranking, start=1):
            scores[article_id] = scores.get(article_id, 0) + weight / (k + position)
    return sorted(scores, key=scores.get, reverse=True)
