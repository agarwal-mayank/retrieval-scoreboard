"""Rerank the hybrid 70/30 shortlist on WixQA with Claude Haiku.

Uses the saved hybrid top 10 (runs/results/hybrid_w70-30_wixqa.json, from
scripts/run_wixqa.py), so nothing is searched or embedded again.

    uv run --env-file .env python scripts/run_hybrid_rerank_wixqa.py

Prints a cost estimate first and stops if the US$1 budget would be passed.
"""

import json
import time

from scoreboard.report import print_report, save, summarize
from scoreboard.rerank import HaikuReranker, check_haiku_budget, record_spend
from scoreboard.wixqa import load_wixqa

articles, questions = load_wixqa()
by_id = {a["id"]: a for a in articles}
titles = {a["id"]: a["title"] for a in articles}
hybrid = json.load(open("runs/results/hybrid_w70-30_wixqa.json", encoding="utf-8"))["results"]


def shortlist(q):
    return [by_id[i] for i in hybrid[q["id"]][:10]]


haiku = HaikuReranker()
check_haiku_budget([haiku.prompt(q["question"], shortlist(q)) for q in questions])

results, seconds = {}, []
try:
    for n, q in enumerate(questions, start=1):
        started = time.monotonic()
        reranked = haiku.rerank(q["question"], shortlist(q))
        seconds.append(time.monotonic() - started)
        results[q["id"]] = [a["id"] for a in reranked]
        if n % 50 == 0:
            print(f"  {n}/{len(questions)}", flush=True)
finally:
    record_spend(haiku.cost)

summary = summarize(results, questions, exam="wixqa", method=f"Hybrid 70/30 top 10 + rerank ({haiku.model})")
summary["reranker"] = {"model": haiku.model, "max_words_per_article": haiku.max_words, "effort": "low", "shortlist": "hybrid 70/30"}
summary["usage"] = {"input_tokens": haiku.input_tokens, "output_tokens": haiku.output_tokens, "cost_usd": round(haiku.cost, 4)}
summary["avg_seconds_per_question"] = round(sum(seconds) / len(seconds), 2)
summary["fallbacks"] = haiku.fallbacks
print_report(summary, results, questions, titles)
print(f"\n{summary['avg_seconds_per_question']}s per question, unreadable replies: {haiku.fallbacks}")
print(f"Haiku usage: {haiku.input_tokens:,} input, {haiku.output_tokens:,} output tokens, ${haiku.cost:.4f}")
save(summary, results, "rerank_haiku_hybrid")
