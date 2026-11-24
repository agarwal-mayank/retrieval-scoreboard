"""Level 4: rerank vector search's top 10 with a local LLM (qwen2.5 in Ollama).

Run from the repo root (Ollama running, both models pulled):

    uv run python scripts/run_rerank.py               # exam v1 (30 questions)
    uv run python scripts/run_rerank.py --exam v2   # exam v2 (60 questions)

Vector search finds 10 candidates; qwen re-orders them; the top 5 are scored.
Also reports seconds per question and how often the reply couldn't be read.
"""

import sys
import time

from scoreboard.embeddings import OllamaEmbedder, load_or_build_article_vectors
from scoreboard.report import exam_from_args, load_jsonl, print_report, save, summarize
from scoreboard.rerank import OllamaReranker
from scoreboard.vector_search import top_k

SHORTLIST = 10

articles = load_jsonl("data/articles.jsonl")
exam, questions = exam_from_args(sys.argv)
by_id = {a["id"]: a for a in articles}
titles = {a["id"]: a["title"] for a in articles}

embedder = OllamaEmbedder()
article_vectors = load_or_build_article_vectors(embedder, articles, "runs/embeddings")
query_vectors = embedder.embed_queries([q["question"] for q in questions])
reranker = OllamaReranker()

results, seconds = {}, []
for n, (q, v) in enumerate(zip(questions, query_vectors), start=1):
    shortlist = [by_id[i] for i in top_k(v, article_vectors, k=SHORTLIST)]
    started = time.monotonic()
    reranked = reranker.rerank(q["question"], shortlist)
    seconds.append(time.monotonic() - started)
    results[q["id"]] = [a["id"] for a in reranked][:5]
    print(f"  {n}/{len(questions)} {q['id']} reranked in {seconds[-1]:.1f}s", flush=True)

summary = summarize(results, questions, exam=exam, method=f"Vector top {SHORTLIST} + rerank ({reranker.model})")
summary["reranker"] = {"model": reranker.model, "digest": reranker.digest, "temperature": 0}
summary["avg_seconds_per_question"] = round(sum(seconds) / len(seconds), 2)
summary["fallbacks"] = reranker.fallbacks
print_report(summary, results, questions, titles)
print(f"\nAverage rerank time: {summary['avg_seconds_per_question']}s per question. Unreadable replies (kept vector order): {reranker.fallbacks}")
save(summary, results, f"rerank_{reranker.model.replace(':', '-')}")
