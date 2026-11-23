"""Head-to-head: compare two methods' saved answer sheets, question by question.

Run from the repo root, after both methods have been run:

    uv run python scripts/compare_methods.py runs/results/vector_nomic-embed-text_0a109f422b47_v1.json runs/results/bm25_v1.json

For each question: the right article's rank under each method (or "-" if it
missed the top 5), and who ranked it higher. Then a tally by question type.
"""

import json
import sys
from collections import Counter, defaultdict

from scoreboard.report import EXAMS, TYPES, load_jsonl


def rank(ranked, answer_id):
    """1-based rank of the right article, or None if it isn't in the list."""
    return ranked.index(answer_id) + 1 if answer_id in ranked else None


def winner(rank_a, rank_b):
    if rank_a is None and rank_b is None:
        return "both miss"
    if rank_a == rank_b:
        return "tie"
    if rank_b is None or (rank_a is not None and rank_a < rank_b):
        return "A"
    return "B"


path_a, path_b = sys.argv[1], sys.argv[2]
run_a = json.loads(open(path_a, encoding="utf-8").read())
run_b = json.loads(open(path_b, encoding="utf-8").read())
name_a, name_b = run_a["summary"]["method"], run_b["summary"]["method"]
exam = run_a["summary"]["exam"]
if run_b["summary"]["exam"] != exam:
    raise SystemExit("These two runs used different exams, so they can't be compared question by question.")
questions = load_jsonl(EXAMS[exam])

print(f"\nA = {name_a}\nB = {name_b}\n")
print(f"  {'Q':<4} {'type':<11} {'A':>3} {'B':>3}  winner")
tally = defaultdict(Counter)
for q in questions:
    a = rank(run_a["results"][q["id"]], q["answer_article_id"])
    b = rank(run_b["results"][q["id"]], q["answer_article_id"])
    w = winner(a, b)
    tally[q["type"]][w] += 1
    tally["overall"][w] += 1
    print(f"  {q['id']:<4} {q['type']:<11} {a or '-':>3} {b or '-':>3}  {w}")

print(f"\n  {'':<11} {'A wins':>7} {'B wins':>7} {'tie':>5} {'both miss':>10}")
for t in TYPES + ["overall"]:
    c = tally[t]
    print(f"  {t:<11} {c['A']:>7} {c['B']:>7} {c['tie']:>5} {c['both miss']:>10}")
