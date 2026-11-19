"""Vector search: rank articles by how closely their meaning matches a question."""

import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """How closely two vectors point the same way: 1.0 same, 0.0 unrelated, -1.0 opposite.

    Recipe: dot product (multiply matching numbers, add them up)
    divided by (length of a x length of b), where length = sqrt(sum of squares).
    Raise ValueError if either vector has zero length (the direction is undefined).
    """
    dot = sum(x * y for x, y in zip(a, b))
    length_a = math.sqrt(sum(x * x for x in a))
    length_b = math.sqrt(sum(x * x for x in b))
    if length_a == 0 or length_b == 0:
        raise ValueError("A zero vector has no direction")
    return dot / (length_a * length_b)


def top_k(query_vector: list[float], article_vectors: dict[str, list[float]], k: int = 5) -> list[str]:
    """The ids of the k articles most similar to query_vector, best first.

    article_vectors: article id -> vector, e.g. {"KB0001": [0.1, 0.3, ...], ...}
    If there are fewer than k articles, return them all (still best first).
    """
    scores = {}
    for article_id, vector in article_vectors.items():
        scores[article_id] = cosine_similarity(query_vector, vector)
    ranked = sorted(scores, key=scores.get, reverse=True)
    return ranked[:k]
