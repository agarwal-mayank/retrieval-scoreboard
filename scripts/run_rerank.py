"""Level 4: rerank vector search's top 10 with a local LLM (qwen2.5 in Ollama).

Run from the repo root (Ollama running, both models pulled):

    uv run python scripts/run_rerank.py               # exam v1 (30 questions)
    uv run python scripts/run_rerank.py --exam v2   # exam v2 (60 questions)
    uv run --env-file .env python scripts/run_rerank.py --reranker haiku   # Claude Haiku as the judge

Vector search finds 10 candidates; qwen (or Haiku) re-orders them; the top 5 are scored.
Also reports seconds per question and how often the reply couldn't be read.
Haiku runs print a cost estimate first and stop if the project's US$1 budget would be passed.
"""

import sys
import time

from scoreboard.embeddings import OllamaEmbedder, load_or_build_article_vectors
from scoreboard.report import exam_from_args, load_jsonl, print_report, save, summarize
from scoreboard.rerank import HaikuReranker, OllamaReranker, check_haiku_budget, record_spend
from scoreboard.vector_search import top_k

SHORTLIST = 10

articles = load_jsonl("data/articles.jsonl")
exam, questions = exam_from_args(sys.argv)
by_id = {a["id"]: a for a in articles}
titles = {a["id"]: a["title"] for a in articles}

embedder = OllamaEmbedder()
article_vectors = load_or_build_article_vectors(embedder, articles, "runs/embeddings")
query_vectors = embedder.embed_queries([q["question"] for q in questions])
name = sys.argv[sys.argv.index("--reranker") + 1] if "--reranker" in sys.argv else "qwen"
if name not in ("qwen", "haiku"):
    raise SystemExit(f"Unknown reranker '{name}'. Choose qwen or haiku.")
reranker = HaikuReranker() if name == "haiku" else OllamaReranker()
shortlists = [[by_id[i] for i in top_k(v, article_vectors, k=SHORTLIST)] for v in query_vectors]
if name == "haiku":
    check_haiku_budget([reranker.prompt(q["question"], s) for q, s in zip(questions, shortlists)])

results, seconds = {}, []
try:
    for n, (q, shortlist) in enumerate(zip(questions, shortlists), start=1):
        started = time.monotonic()
        reranked = reranker.rerank(q["question"], shortlist)
        seconds.append(time.monotonic() - started)
        results[q["id"]] = [a["id"] for a in reranked][:5]
        print(f"  {n}/{len(questions)} {q['id']} reranked in {seconds[-1]:.1f}s", flush=True)
finally:
    if name == "haiku":
        record_spend(reranker.cost)

summary = summarize(results, questions, exam=exam, method=f"Vector top {SHORTLIST} + rerank ({reranker.model})")
if name == "haiku":
    summary["reranker"] = {"model": reranker.model, "max_words_per_article": reranker.max_words, "effort": "low"}
    summary["usage"] = {
        "input_tokens": reranker.input_tokens,
        "output_tokens": reranker.output_tokens,
        "cost_usd": round(reranker.cost, 4),
    }
else:
    summary["reranker"] = {"model": reranker.model, "digest": reranker.digest, "temperature": 0}
summary["avg_seconds_per_question"] = round(sum(seconds) / len(seconds), 2)
summary["fallbacks"] = reranker.fallbacks
print_report(summary, results, questions, titles)
print(f"\nAverage rerank time: {summary['avg_seconds_per_question']}s per question. Unreadable replies (kept vector order): {reranker.fallbacks}")
if name == "haiku":
    print(f"Haiku usage: {reranker.input_tokens:,} input, {reranker.output_tokens:,} output tokens, ${reranker.cost:.4f}")
save(summary, results, "rerank_haiku" if name == "haiku" else f"rerank_{reranker.model.replace(':', '-')}")
