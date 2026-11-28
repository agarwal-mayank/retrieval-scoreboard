"""Shared scoreboard report: the same metrics and printout for every search method."""

import json
from collections import defaultdict
from pathlib import Path

from scoreboard.scoring import credit_acceptable, hit_at_k, is_hit, mean_ndcg_at_k, mean_recall_at_k, mrr

TYPES = ["easy", "paraphrase", "near-twin", "messy"]
EXAMS = {"v1": "data/questions.jsonl", "v2": "data/questions_v2.jsonl"}


def exam_from_args(argv):
    """`--exam v2` picks exam v2; the default is v1."""
    exam = argv[argv.index("--exam") + 1] if "--exam" in argv else "v1"
    if exam not in EXAMS:
        raise SystemExit(f"Unknown exam '{exam}'. Choose from: {', '.join(EXAMS)}")
    return exam, load_jsonl(EXAMS[exam])


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def metrics(results, key):
    """hit@5, hit@1 and MRR for one answer key (all questions, or one type)."""
    return {
        "questions": len(key),
        "hit@5": hit_at_k(results, key, k=5),
        "hit@1": hit_at_k(results, key, k=1),
        "mrr": mrr({i: r[:5] for i, r in results.items()}, key),  # MRR over the top 5
    }


def standard_metrics(results, questions):
    """Recall@5 and nDCG@10, the field's standard retrieval metrics, over these questions."""
    return {
        "questions": len(questions),
        "recall@5": mean_recall_at_k(results, questions, k=5),
        "ndcg@10": mean_ndcg_at_k(results, questions, k=10),
    }


def summarize(results, questions, method, exam="v1"):
    answers = {q["id"]: q["answer_article_id"] for q in questions}
    by_type = defaultdict(dict)
    for q in questions:
        by_type[q["type"]][q["id"]] = q["answer_article_id"]
    # The v1/v2 types in their usual order, then any others (e.g. WixQA's expert, simulated).
    types = [t for t in TYPES if t in by_type] + [t for t in by_type if t not in TYPES]
    summary = {
        "method": method,
        "exam": exam,
        "overall": metrics(results, answers),
        "by_type": {t: metrics(results, by_type[t]) for t in types},
    }
    # Standard metrics that count every correct article (answer + also_relevant).
    by_type_questions = defaultdict(list)
    for q in questions:
        by_type_questions[q["type"]].append(q)
    summary["standard"] = {
        "overall": standard_metrics(results, questions),
        "by_type": {t: standard_metrics(results, by_type_questions[t]) for t in types},
    }
    if any(q.get("also_relevant") for q in questions):
        # Lenient marking: an acceptable twin article also counts as right.
        lenient = credit_acceptable(results, questions)
        summary["overall_lenient"] = metrics(lenient, answers)
        if not set(types) <= set(TYPES):
            summary["by_type_lenient"] = {t: metrics(lenient, by_type[t]) for t in types}
    return summary


def print_report(summary, results, questions, titles):
    print(f"\n{summary['method']}, exam {summary['exam']}\n")
    print(f"  {'':<11} {'n':>3}  {'hit@5':>6}  {'hit@1':>6}  {'MRR':>5}")
    rows = [("overall", summary["overall"])] + list(summary["by_type"].items())
    if "overall_lenient" in summary:
        rows.append(("lenient*", summary["overall_lenient"]))
    for t, m in summary.get("by_type_lenient", {}).items():
        rows.append((f"lenient {t}"[:11], m))
    for label, m in rows:
        print(f"  {label:<11} {m['questions']:>3}  {m['hit@5']:6.1%}  {m['hit@1']:6.1%}  {m['mrr']:5.3f}")
    if "overall_lenient" in summary:
        print("  * overall, counting an acceptable twin article (also_relevant) as right")
    std = summary["standard"]["overall"]
    print(f"  standard (all correct articles): Recall@5 {std['recall@5']:.3f}, nDCG@10 {std['ndcg@10']:.3f}")

    both = [q for q in questions if q.get("also_relevant")]
    if both:
        found = sum(
            is_hit(results[q["id"]], q["answer_article_id"])
            and all(a in results[q["id"]][:5] for a in q["also_relevant"])
            for q in both
        )
        print(f"\n  questions with also_relevant articles, all of them in the top 5 too: {found} of {len(both)}")

    misses = [q for q in questions if not is_hit(results[q["id"]], q["answer_article_id"])]
    print(f"\nMisses from the top 5 ({len(misses)}):")
    for q in misses:
        print(f"  {q['id']} [{q['type']}] {q['question']}")
        print(f"      wanted {q['answer_article_id']} {titles[q['answer_article_id']]}")
        print(f"      got #1 {results[q['id']][0]} {titles[results[q['id']][0]]}")

    not_first = [
        q for q in questions
        if is_hit(results[q["id"]], q["answer_article_id"]) and results[q["id"]][0] != q["answer_article_id"]
    ]
    print(f"\nIn the top 5 but not #1 ({len(not_first)}):")
    for q in not_first:
        rank = results[q["id"]].index(q["answer_article_id"]) + 1
        print(f"  {q['id']} [{q['type']}] rank {rank}: {q['question']}")
        print(f"      #1 was {results[q['id']][0]} {titles[results[q['id']][0]]}")


def save(summary, results, name):
    out = Path("runs/results")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}_{summary['exam']}.json"
    path.write_text(json.dumps({"summary": summary, "results": results}, indent=2) + "\n", encoding="utf-8")
    return path
