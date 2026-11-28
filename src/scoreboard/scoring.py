"""The referee: scores a search method's results against the answer key."""


import math


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


def credit_acceptable(results: dict[str, list[str]], questions: list[dict]) -> dict[str, list[str]]:
    """Lenient marking: treat any also_relevant article as the right answer.

    Returns a copy of results where each also_relevant id is replaced by the
    question's answer id (keeping its position), so hit_at_k and mrr can be
    reused unchanged. Questions without also_relevant are left as they are.
    """
    credited = {}
    for q in questions:
        ranked = results.get(q["id"], [])
        acceptable = set(q.get("also_relevant", []))
        swapped = [q["answer_article_id"] if r in acceptable else r for r in ranked]
        credited[q["id"]] = list(dict.fromkeys(swapped))  # drop repeats, keep first position
    return credited


def recall_at_k(ranked: list[str], relevant: set[str], k: int = 5) -> float:
    """Share of the relevant articles that appear in the top k, from 0.0 to 1.0.

    With one relevant article this is the same as is_hit (1.0 or 0.0).
    Raise ValueError if relevant is empty.
    """
    if not relevant:
        raise ValueError("No relevant articles to find")
    return len(set(ranked[:k]) & relevant) / len(relevant)


def ndcg_at_k(ranked: list[str], relevant: set[str], k: int = 10) -> float:
    """Normalised discounted cumulative gain for one question, from 0.0 to 1.0.

    Gain: each relevant article in the top k earns points.
    Discounted: an article at position p (counting from 1) earns 1 / log2(p + 1),
        so #1 earns 1.0, #2 earns 0.63, #3 earns 0.5, #10 earns 0.29.
    Normalised: divide by the best possible score, which is every relevant
        article at the very top (only the first k positions count).
    Raise ValueError if relevant is empty.
    """
    if not relevant:
        raise ValueError("No relevant articles to find")
    dcg = 0.0
    for position, article_id in enumerate(ranked[:k], start=1):
        if article_id in relevant:
            dcg += 1 / math.log2(position + 1)
    ideal = sum(1 / math.log2(p + 1) for p in range(1, min(len(relevant), k) + 1))
    return dcg / ideal

def relevant_set(question: dict) -> set[str]:
    """All correct articles for a question: the answer plus any also_relevant."""
    return {question["answer_article_id"], *question.get("also_relevant", [])}


def mean_recall_at_k(results: dict[str, list[str]], questions: list[dict], k: int = 5) -> float:
    """recall_at_k averaged over questions (a question missing from results scores 0)."""
    return sum(recall_at_k(results.get(q["id"], []), relevant_set(q), k) for q in questions) / len(questions)


def mean_ndcg_at_k(results: dict[str, list[str]], questions: list[dict], k: int = 10) -> float:
    """ndcg_at_k averaged over questions (a question missing from results scores 0)."""
    return sum(ndcg_at_k(results.get(q["id"], []), relevant_set(q), k) for q in questions) / len(questions)
