"""The referee: scores a search method's results against the answer key."""


def is_hit(ranked_ids: list[str], answer_id: str, k: int = 5) -> bool:
    """True if answer_id is among the first k ids in ranked_ids.

    ranked_ids is a search method's results for one question, best first,
    e.g. ["KB0102", "KB0112", "KB0103"].
    """
    return answer_id in ranked_ids[:k]


def hit_at_k(results: dict[str, list[str]], answers: dict[str, str], k: int = 5) -> float:
    """Share of questions whose right article is in the top k, from 0.0 to 1.0.

    results: question id -> ranked article ids, e.g. {"Q01": ["KB0011", ...]}
    answers: question id -> the right article id, e.g. {"Q01": "KB0011"}

    A question missing from results counts as a miss.
    Raise ValueError if answers is empty (there's nothing to score).
    """
    if not answers:
        raise ValueError("No questions to score")
    hits = 0
    for question_id, answer_id in answers.items():
        ranked = results.get(question_id, [])
        if is_hit(ranked, answer_id, k):
            hits += 1
    return hits / len(answers)
