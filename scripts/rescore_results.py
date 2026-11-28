"""Re-score saved answer sheets with the current metrics, without re-running any search.

Run from the repo root after the run scripts have saved their results:

    uv run python scripts/rescore_results.py

Reads every runs/results/*.json, recomputes its summary (hit@5, hit@1, MRR,
Recall@5, nDCG@10) from the saved rankings, writes it back, and prints a table.
Results saved with only a top 5 give a lower nDCG@10 than they should; re-run
those methods first (the run scripts now keep the top 10).
"""

import json
from pathlib import Path

from scoreboard.report import EXAMS, load_jsonl, summarize
from scoreboard.wixqa import load_wixqa

questions_for = {exam: load_jsonl(path) for exam, path in EXAMS.items()}

rows = []
for path in sorted(Path("runs/results").glob("*.json")):
    run = json.loads(path.read_text(encoding="utf-8"))
    old, results = run["summary"], run["results"]
    exam = old["exam"]
    if exam == "wixqa":
        questions_for.setdefault("wixqa", load_wixqa()[1])
    questions = questions_for[exam]
    depth = min(len(r) for r in results.values())
    new = summarize(results, questions, method=old["method"], exam=exam)
    for key, value in old.items():  # keep extra details (weights, reranker, usage...)
        new.setdefault(key, value)
    run["summary"] = new
    path.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
    rows.append((exam, path.stem, depth, new))

print(f"{'exam':<6} {'run':<44} {'depth':>5}  {'hit@5':>6}  {'hit@1':>6}  {'MRR':>5}  {'R@5':>5}  {'nDCG@10':>7}")
for exam, name, depth, s in rows:
    o, std = s["overall"], s["standard"]["overall"]
    print(f"{exam:<6} {name:<44} {depth:>5}  {o['hit@5']:6.1%}  {o['hit@1']:6.1%}  {o['mrr']:5.3f}  {std['recall@5']:5.3f}  {std['ndcg@10']:7.3f}")
