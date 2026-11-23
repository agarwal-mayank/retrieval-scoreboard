"""Checks exam v2 is complete, matches its frozen random plan, and is fresh ground."""

import json
from collections import Counter
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parent.parent / "data"
REQUIRED = {"id", "question", "answer_article_id", "type"}


def load(name):
    with open(DATA / name, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


@pytest.fixture(scope="module")
def questions():
    return load("questions_v2.jsonl")


@pytest.fixture(scope="module")
def articles():
    return {a["id"]: a for a in load("articles.jsonl")}


@pytest.fixture(scope="module")
def plan():
    return json.loads((DATA / "questions_v2_targets.json").read_text(encoding="utf-8"))


def test_has_60_questions(questions):
    assert len(questions) == 60


def test_required_fields(questions):
    for q in questions:
        assert REQUIRED <= set(q) <= REQUIRED | {"also_relevant"}, q["id"]
        assert all(isinstance(q[k], str) and q[k].strip() for k in REQUIRED)


def test_ids_and_texts_are_unique(questions):
    assert len({q["id"] for q in questions}) == 60
    assert len({q["question"].lower() for q in questions}) == 60


def test_answers_and_also_relevant_exist(questions, articles):
    for q in questions:
        assert q["answer_article_id"] in articles, q["id"]
        for extra in q.get("also_relevant", []):
            assert extra in articles and extra != q["answer_article_id"], q["id"]


def test_matches_the_frozen_random_plan(questions, plan):
    planned = {t["id"]: (t["answer_article_id"], t["type"]) for t in plan["targets"]}
    assert {q["id"]: (q["answer_article_id"], q["type"]) for q in questions} == planned


def test_six_per_category(questions, articles):
    counts = Counter(articles[q["answer_article_id"]]["category"] for q in questions)
    assert len(counts) == 10 and set(counts.values()) == {6}


def test_type_mix(questions):
    assert Counter(q["type"] for q in questions) == {"easy": 6, "paraphrase": 18, "near-twin": 18, "messy": 18}


def test_no_overlap_with_v1_answers(questions):
    v1 = load("questions.jsonl")
    used = {q["answer_article_id"] for q in v1} | {a for q in v1 for a in q.get("also_relevant", [])}
    assert not used & {q["answer_article_id"] for q in questions}
