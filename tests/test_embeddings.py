"""Tests for the article-vector cache, using a fake embedder (no Ollama needed)."""

import json

from scoreboard.embeddings import article_text, load_or_build_article_vectors


class FakeEmbedder:
    name = "fake_0001"
    document_prefix = "search_document: "

    def __init__(self):
        self.calls = 0
        self.seen = []

    def embed_documents(self, texts):
        self.calls += 1
        self.seen = [self.document_prefix + t for t in texts]
        return [[float(len(t)), 1.0] for t in texts]


ARTICLES = [
    {"id": "KB0001", "title": "Forgot my password", "body": "Reset it."},
    {"id": "KB0002", "title": "Printer offline", "body": "Restart it."},
]


def test_article_text_is_title_then_body():
    assert article_text(ARTICLES[0]) == "Forgot my password\n\nReset it."


def test_builds_vectors_for_every_article(tmp_path):
    vectors = load_or_build_article_vectors(FakeEmbedder(), ARTICLES, tmp_path)
    assert list(vectors) == ["KB0001", "KB0002"]
    assert all(len(v) == 2 for v in vectors.values())


def test_writes_cache_and_recipe(tmp_path):
    load_or_build_article_vectors(FakeEmbedder(), ARTICLES, tmp_path)
    assert (tmp_path / "fake_0001.jsonl").exists()
    meta = json.loads((tmp_path / "fake_0001.meta.json").read_text(encoding="utf-8"))
    assert meta["articles"] == 2 and meta["dimensions"] == 2


def test_second_run_reuses_the_cache(tmp_path):
    embedder = FakeEmbedder()
    first = load_or_build_article_vectors(embedder, ARTICLES, tmp_path)
    second = load_or_build_article_vectors(embedder, ARTICLES, tmp_path)
    assert embedder.calls == 1
    assert first == second


def test_cache_is_rebuilt_when_articles_change(tmp_path):
    embedder = FakeEmbedder()
    load_or_build_article_vectors(embedder, ARTICLES, tmp_path)
    load_or_build_article_vectors(embedder, ARTICLES[:1], tmp_path)
    assert embedder.calls == 2
