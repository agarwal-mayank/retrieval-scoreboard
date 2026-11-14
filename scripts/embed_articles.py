"""Embed the article library with nomic-embed-text in your local Ollama.

Run from the repo root (Ollama must be running, model pulled):

    uv run python scripts/embed_articles.py

Vectors go to runs/embeddings/ (git-ignored). Re-running reuses them.
"""

import json
import time

from scoreboard.embeddings import OllamaEmbedder, load_or_build_article_vectors

with open("data/articles.jsonl", encoding="utf-8") as f:
    articles = [json.loads(line) for line in f]

embedder = OllamaEmbedder()
print(f"Embedder: {embedder.name} (digest {embedder.digest[:12]})")

started = time.monotonic()
vectors = load_or_build_article_vectors(embedder, articles, "runs/embeddings")
seconds = time.monotonic() - started

dims = len(next(iter(vectors.values())))
print(f"{len(vectors)} articles x {dims} numbers in {seconds:.1f}s -> runs/embeddings/{embedder.name}.jsonl")
