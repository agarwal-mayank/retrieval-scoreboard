"""Pick the target articles and question types for exam v2, at random.

Neither the question writers nor any search result decide which articles get
questions: a fixed seed does. Articles already used as v1 answers are skipped,
so v2 covers fresh ground.

    uv run python scripts/pick_v2_targets.py

Writes data/questions_v2_targets.json (committed, so the plan is frozen
before any question is written).
"""

import json
import random

from scoreboard.report import load_jsonl

SEED = 2026
PER_CATEGORY = 6
MIX = {"easy": 6, "paraphrase": 18, "near-twin": 18, "messy": 18}

articles = load_jsonl("data/articles.jsonl")
v1 = load_jsonl("data/questions.jsonl")
used = {q["answer_article_id"] for q in v1} | {a for q in v1 for a in q.get("also_relevant", [])}

rng = random.Random(SEED)
targets = []
for category in sorted({a["category"] for a in articles}):
    pool = [a for a in articles if a["category"] == category and a["id"] not in used]
    targets.extend(sorted(rng.sample(pool, PER_CATEGORY), key=lambda a: a["id"]))

types = [t for t, n in MIX.items() for _ in range(n)]
rng.shuffle(types)

plan = [
    {"id": f"V{i:02d}", "answer_article_id": a["id"], "category": a["category"], "title": a["title"], "type": t}
    for i, (a, t) in enumerate(zip(targets, types), start=1)
]
with open("data/questions_v2_targets.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump({"seed": SEED, "mix": MIX, "excluded_v1_articles": sorted(used), "targets": plan}, f, indent=2)
    f.write("\n")

for p in plan:
    print(f"{p['id']}  {p['type']:<10}  {p['answer_article_id']}  {p['category']:<28} {p['title']}")
