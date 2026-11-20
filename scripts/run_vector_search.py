"""Level 2: run vector search on the 30-question exam and score it.

Run from the repo root (Ollama running, model pulled):

    uv run python scripts/run_vector_search.py

Prints hit@5 overall and by question type, lists every miss, and saves the
answer sheet to runs/results/ for the scoreboard.
"""

import json
from collections import defaultdict
from pathlib import Path

from scoreboard.embeddings import OllamaEmbedder, load_or_build_article_vectors
from scoreboard.scoring import hit_at_k, is_hit, mrr
from scoreboard.vector_search import top_k

TYPES = ["easy", "paraphrase", "near-twin", "messy"]

with open("data/articles.jsonl", encoding="utf-8") as f:
    articles = [json.loads(line) for line in f]
with open("data/questions.jsonl", encoding="utf-8") as f:
    questions = [json.loads(line) for line in f]
titles = {a["id"]: a["title"] for a in articles}

embedder = OllamaEmbedder()
article_vectors = load_or_build_article_vectors(embedder, articles, "runs/embeddings")
query_vectors = embedder.embed_queries([q["question"] for q in questions])

results = {q["id"]: top_k(v, article_vectors, k=5) for q, v in zip(questions, query_vectors)}
answers = {q["id"]: q["answer_article_id"] for q in questions}

def metrics(key):
    """hit@5, hit@1 and MRR for one answer key (all questions, or one type)."""
    return {
        "questions": len(key),
        "hit@5": hit_at_k(results, key, k=5),
        "hit@1": hit_at_k(results, key, k=1),
        "mrr": mrr(results, key),
    }


by_type = defaultdict(dict)
for q in questions:
    by_type[q["type"]][q["id"]] = q["answer_article_id"]
summary = {"method": "vector", "embedder": embedder.name, "exam": "v1", "overall": metrics(answers)}
summary["by_type"] = {t: metrics(by_type[t]) for t in TYPES}

print(f"\nVector search ({embedder.name}), exam v1\n")
print(f"  {'':<11} {'n':>3}  {'hit@5':>6}  {'hit@1':>6}  {'MRR':>5}")
for label, m in [("overall", summary["overall"])] + list(summary["by_type"].items()):
    print(f"  {label:<11} {m['questions']:>3}  {m['hit@5']:6.1%}  {m['hit@1']:6.1%}  {m['mrr']:5.3f}")

both = [q for q in questions if q.get("also_relevant")]
if both:
    found = sum(all(a in results[q["id"]] for a in q["also_relevant"]) and is_hit(results[q["id"]], q["answer_article_id"]) for q in both)
    print(f"\n  two-intent questions with both articles in the top 5: {found} of {len(both)}")

misses = [q for q in questions if not is_hit(results[q["id"]], q["answer_article_id"])]
print(f"\nMisses from the top 5 ({len(misses)}):")
for q in misses:
    print(f"  {q['id']} [{q['type']}] {q['question']}")
    print(f"      wanted {q['answer_article_id']} {titles[q['answer_article_id']]}")
    print(f"      got #1 {results[q['id']][0]} {titles[results[q['id']][0]]}")

out = Path("runs/results")
out.mkdir(parents=True, exist_ok=True)
(out / f"vector_{embedder.name}_v1.json").write_text(
    json.dumps({"summary": summary, "results": results}, indent=2) + "\n", encoding="utf-8"
)

# Questions where the right article made the top 5 but not #1: the room for improvement.
not_first = [q for q in questions if results[q["id"]][0] != q["answer_article_id"] and is_hit(results[q["id"]], q["answer_article_id"])]
print(f"\nIn the top 5 but not #1 ({len(not_first)}):")
for q in not_first:
    rank = results[q["id"]].index(q["answer_article_id"]) + 1
    print(f"  {q['id']} [{q['type']}] rank {rank}: {q['question']}")
    print(f"      #1 was {results[q['id']][0]} {titles[results[q['id']][0]]}")
