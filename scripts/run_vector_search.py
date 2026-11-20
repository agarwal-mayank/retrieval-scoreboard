"""Level 2: run vector search on the 30-question exam and score it.

Run from the repo root (Ollama running, model pulled):

    uv run python scripts/run_vector_search.py

Prints hit@5, hit@1 and MRR overall and by question type, lists the misses,
and saves the answer sheet to runs/results/ for the scoreboard.
"""

from scoreboard.embeddings import OllamaEmbedder, load_or_build_article_vectors
from scoreboard.report import load_jsonl, print_report, save, summarize
from scoreboard.vector_search import top_k

articles = load_jsonl("data/articles.jsonl")
questions = load_jsonl("data/questions.jsonl")
titles = {a["id"]: a["title"] for a in articles}

embedder = OllamaEmbedder()
article_vectors = load_or_build_article_vectors(embedder, articles, "runs/embeddings")
query_vectors = embedder.embed_queries([q["question"] for q in questions])
results = {q["id"]: top_k(v, article_vectors, k=5) for q, v in zip(questions, query_vectors)}

summary = summarize(results, questions, method=f"Vector search ({embedder.name})")
summary["embedder"] = embedder.name
print_report(summary, results, questions, titles)
save(summary, results, f"vector_{embedder.name}")
