"""Level 3: run BM25 keyword search on the 30-question exam and score it.

Run from the repo root (no Ollama or API key needed):

    uv run python scripts/run_bm25_search.py

Prints hit@5, hit@1 and MRR overall and by question type, lists the misses,
and saves the answer sheet to runs/results/ for the scoreboard.
"""

from scoreboard.keyword_search import BM25Index
from scoreboard.report import load_jsonl, print_report, save, summarize

articles = load_jsonl("data/articles.jsonl")
questions = load_jsonl("data/questions.jsonl")
titles = {a["id"]: a["title"] for a in articles}

index = BM25Index(articles)
results = {q["id"]: index.top_k(q["question"], k=5) for q in questions}

summary = summarize(results, questions, method="Keyword search (BM25)")
print_report(summary, results, questions, titles)
save(summary, results, "bm25")
