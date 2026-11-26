"""Level 5 prep: the real-world round. Run every method on WixQA's 400 questions.

Download the three WixQA files into runs/wixqa/ first (see README), then, with
Ollama running and the API key loaded:

    uv run --env-file .env python scripts/run_wixqa.py

Methods: vector, BM25, hybrid (equal and 70/30, top 20 each), and vector top 10
reranked by Claude Haiku and by local qwen. Articles can have several right
answers, so the lenient numbers are the headline; strict is shown too.
The embedding cache (runs/embeddings/wixqa) makes re-runs fast.
"""

import time

from scoreboard.embeddings import OllamaEmbedder, load_or_build_article_vectors
from scoreboard.fusion import rrf
from scoreboard.keyword_search import BM25Index
from scoreboard.report import print_report, save, summarize
from scoreboard.rerank import HaikuReranker, OllamaReranker, check_haiku_budget, record_spend
from scoreboard.vector_search import top_k
from scoreboard.wixqa import load_wixqa

CANDIDATES = 20  # per method, for the hybrids
SHORTLIST = 10  # vector results handed to a reranker
EXAM = "wixqa"

articles, questions = load_wixqa()
by_id = {a["id"]: a for a in articles}
titles = {a["id"]: a["title"] for a in articles}
print(f"{len(articles)} articles, {len(questions)} questions")


def report(results, method, name, **extra):
    summary = summarize(results, questions, exam=EXAM, method=method)
    summary.update(extra)
    print_report(summary, results, questions, titles)
    save(summary, results, name)


embedder = OllamaEmbedder()
article_vectors = load_or_build_article_vectors(embedder, articles, "runs/embeddings/wixqa")
query_vectors = embedder.embed_queries([q["question"] for q in questions])
bm25 = BM25Index(articles)

vector_ranked = {q["id"]: top_k(v, article_vectors, k=CANDIDATES) for q, v in zip(questions, query_vectors)}
bm25_ranked = {q["id"]: bm25.top_k(q["question"], k=CANDIDATES) for q in questions}

report({i: r[:5] for i, r in vector_ranked.items()}, f"Vector search ({embedder.name})", "vector", embedder=embedder.name)
report(
    {i: r[:5] for i, r in bm25_ranked.items()}, "Keyword search (BM25)", "bm25",
)
for weights, label, name in [(None, "equal weights", "hybrid"), ([0.7, 0.3], "weighted 70% vector / 30% BM25", "hybrid_w70-30")]:
    fused = {i: rrf([vector_ranked[i], bm25_ranked[i]], weights=weights)[:5] for i in vector_ranked}
    report(fused, f"Hybrid ({label}, RRF k=60, top {CANDIDATES} each)", name, weights=weights)


def shortlist(q):
    return [by_id[i] for i in vector_ranked[q["id"]][:SHORTLIST]]


def run_reranker(judge, method, name, **extra):
    results, seconds = {}, []
    for n, q in enumerate(questions, start=1):
        started = time.monotonic()
        reranked = judge.rerank(q["question"], shortlist(q))
        seconds.append(time.monotonic() - started)
        results[q["id"]] = [a["id"] for a in reranked][:5]
        if n % 25 == 0:
            print(f"  {name}: {n}/{len(questions)}", flush=True)
    extra["avg_seconds_per_question"] = round(sum(seconds) / len(seconds), 2)
    extra["fallbacks"] = judge.fallbacks
    if hasattr(judge, "cost"):
        extra["usage"] = {
            "input_tokens": judge.input_tokens,
            "output_tokens": judge.output_tokens,
            "cost_usd": round(judge.cost, 4),
        }
    report(results, method, name, **extra)
    print(f"\n{name}: {extra['avg_seconds_per_question']}s per question, unreadable replies (kept vector order): {judge.fallbacks}")
    return extra


# Haiku: estimate the cost first, and stop if it would pass the budget.
haiku = HaikuReranker()
check_haiku_budget([haiku.prompt(q["question"], shortlist(q)) for q in questions])
try:
    run_reranker(
        haiku, f"Vector top {SHORTLIST} + rerank ({haiku.model})", "rerank_haiku",
        reranker={"model": haiku.model, "max_words_per_article": haiku.max_words, "effort": "low"},
    )
finally:
    record_spend(haiku.cost)
print(f"Haiku usage: {haiku.input_tokens:,} input, {haiku.output_tokens:,} output tokens, ${haiku.cost:.4f}")

qwen = OllamaReranker(max_words=400)
run_reranker(
    qwen, f"Vector top {SHORTLIST} + rerank ({qwen.model})", f"rerank_{qwen.model.replace(':', '-')}",
    reranker={"model": qwen.model, "digest": qwen.digest, "temperature": 0, "max_words_per_article": qwen.max_words},
)
