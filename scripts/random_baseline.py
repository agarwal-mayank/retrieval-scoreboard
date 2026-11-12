"""Score a random-guess baseline: the floor any real search method must beat.

Run from the repo root:

    uv run python scripts/random_baseline.py
"""

import json
import random

from scoreboard.scoring import hit_at_k

SEED = 42  # fixed, so the "random" picks come out the same on every run

# 1. Load the 200 article ids
article_ids = []
with open("data/articles.jsonl", encoding="utf-8") as f:
    for line in f:
        article = json.loads(line)
        article_ids.append(article["id"])

# 2. Load the answer key: question id -> right article id
answers = {}
with open("data/questions.jsonl", encoding="utf-8") as f:
    for line in f:
        question = json.loads(line)
        answers[question["id"]] = question["answer_article_id"]

# 3. The dumbest student: 5 random article ids for every question
rng = random.Random(SEED)
results = {}
for question_id in answers:
    results[question_id] = rng.sample(article_ids, 5)

# 4. Mark the answer sheets with your scorer
score = hit_at_k(results, answers)
hits = round(score * len(answers))
print(f"Random baseline: hit@5 = {score:.1%} ({hits} of {len(answers)} questions)   expected about 2.5%")
