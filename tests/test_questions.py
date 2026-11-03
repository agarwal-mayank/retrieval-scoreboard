"""Checks the 30-question test set is complete and points at real articles."""

import json
from collections import Counter
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parent.parent / "data"


def load(name):
    with open(DATA / name, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


@pytest.fixture(scope="module")
def questions():
    return load("questions.jsonl")


@pytest.fixture(scope="module")
def articles():
    return {a["id"]: a for a in load("articles.jsonl")}


def test_has_30_questions(questions):
    assert len(questions) == 30


REQUIRED = {"id", "question", "answer_article_id", "type"}


def test_every_question_has_the_required_fields(questions):
    for q in questions:
        assert REQUIRED <= set(q) <= REQUIRED | {"also_relevant"}, q["id"]
        assert all(isinstance(q[k], str) and q[k].strip() for k in REQUIRED)


def test_ids_and_texts_are_unique(questions):
    assert len({q["id"] for q in questions}) == len(questions)
    assert len({q["question"].lower() for q in questions}) == len(questions)


def test_every_answer_exists(questions, articles):
    for q in questions:
        assert q["answer_article_id"] in articles, q["id"]
        for extra in q.get("also_relevant", []):
            assert extra in articles and extra != q["answer_article_id"], q["id"]


def test_unanswerable_questions_expect_abstention():
    unanswerable = load("unanswerable.jsonl")
    assert unanswerable
    for u in unanswerable:
        assert u["expected"] == "abstain" and u["question"].strip(), u["id"]


def test_three_questions_per_category(questions, articles):
    counts = Counter(articles[q["answer_article_id"]]["category"] for q in questions)
    assert len(counts) == 10
    assert set(counts.values()) == {3}


def test_type_mix(questions):
    assert Counter(q["type"] for q in questions) == {
        "easy": 8,
        "paraphrase": 12,
        "near-twin": 6,
        "messy": 4,
    }
