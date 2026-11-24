"""Hybrid search: merge several methods' rankings into one."""


def rrf(rankings: list[list[str]], k: int = 60) -> list[str]:
    """Reciprocal Rank Fusion: merge rankings into one list, best first.

    Each ranking votes for its articles: an article at position r (counting
    from 1) gets 1 / (k + r) from that ranking. An article's score is the sum
    of its votes from every ranking it appears in. Articles both methods like
    rise to the top; k (60 is the usual value) stops any single #1 dominating.

    Ties keep the order in which articles were first seen.
    Example: rrf([["A", "B"], ["B", "C"]]) -> ["B", "A", "C"]
    """
    scores = {}
    for ranking in rankings:
        for position, article_id in enumerate(ranking, start=1):
            scores[article_id] = scores.get(article_id, 0) + 1 / (k + position)
    return sorted(scores, key=scores.get, reverse=True)
