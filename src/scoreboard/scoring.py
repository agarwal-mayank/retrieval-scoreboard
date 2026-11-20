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


def mrr(results: dict[str, list[str]], answers: dict[str, str]) -> float:
    """Mean reciprocal rank, from 0.0 to 1.0: rewards putting the right article higher.

    For each question: 1 / (position of the right article), counting from 1.
    So rank 1 scores 1, rank 2 scores 0.5, rank 5 scores 0.2.
    If the right article isn't in that question's results (or the question is
    missing from results), it scores 0. Then average over all questions.
    Raise ValueError if answers is empty.
    """
    if not answers:
        raise ValueError("No questions to score")
    total = 0.0
    for question_id, answer_id in answers.items():
        ranked = results.get(question_id, [])
        if answer_id in ranked:
            rank = ranked.index(answer_id) + 1
            total += 1 / rank
    return total / len(answers)
