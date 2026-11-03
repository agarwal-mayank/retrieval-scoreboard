"""Checks the committed article library is complete and well-formed."""

import json
from collections import Counter
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parent.parent / "data"
ARTICLES = DATA / "articles.jsonl"

pytestmark = pytest.mark.skipif(not ARTICLES.exists(), reason="article library not generated yet")


@pytest.fixture(scope="module")
def articles():
    with open(ARTICLES, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def test_has_200_articles(articles):
    assert len(articles) == 200


def test_every_article_has_the_four_fields(articles):
    for a in articles:
        assert set(a) == {"id", "title", "category", "body"}
        assert all(isinstance(v, str) and v.strip() for v in a.values())


def test_ids_are_unique(articles):
    ids = [a["id"] for a in articles]
    assert len(set(ids)) == len(ids)


def test_titles_are_unique(articles):
    titles = [a["title"].lower() for a in articles]
    assert len(set(titles)) == len(titles)


def test_ten_categories_of_twenty(articles):
    counts = Counter(a["category"] for a in articles)
    assert len(counts) == 10
    assert set(counts.values()) == {20}


def test_body_length_in_range(articles):
    for a in articles:
        assert 100 <= len(a["body"].split()) <= 300, a["id"]


def test_meta_records_how_it_was_made():
    meta = json.loads((DATA / "articles.meta.json").read_text(encoding="utf-8"))
    for key in ("model", "generated_at", "system_prompt", "user_prompt_template", "usage"):
        assert meta[key]
