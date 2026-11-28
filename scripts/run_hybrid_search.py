"""Level 4: hybrid search (vector + BM25, merged with RRF) on an exam.

Run from the repo root (Ollama running, model pulled):

    uv run python scripts/run_hybrid_search.py               # exam v1 (30 questions)
    uv run python scripts/run_hybrid_search.py --exam v2   # exam v2 (60 questions)
    uv run python scripts/run_hybrid_search.py --weights 0.7,0.3   # weighted: vector 70%, BM25 30%

Each method contributes its top 20; Reciprocal Rank Fusion merges them and
the top 5 are scored. Saves the answer sheet to runs/results/.
"""

import sys

from scoreboard.embeddings import OllamaEmbedder, load_or_build_article_vectors
from scoreboard.fusion import rrf
from scoreboard.keyword_search import BM25Index
from scoreboard.report import exam_from_args, load_jsonl, print_report, save, summarize
from scoreboard.vector_search import top_k

CANDIDATES = 20  # how many results each method hands to the fusion

weights = None
if "--weights" in sys.argv:
    weights = [float(w) for w in sys.argv[sys.argv.index("--weights") + 1].split(",")]

articles = load_jsonl("data/articles.jsonl")
exam, questions = exam_from_args(sys.argv)
titles = {a["id"]: a["title"] for a in articles}

embedder = OllamaEmbedder()
article_vectors = load_or_build_article_vectors(embedder, articles, "runs/embeddings")
query_vectors = embedder.embed_queries([q["question"] for q in questions])
bm25 = BM25Index(articles)

results = {}
for q, v in zip(questions, query_vectors):
    vector_ranking = top_k(v, article_vectors, k=CANDIDATES)
    keyword_ranking = bm25.top_k(q["question"], k=CANDIDATES)
    results[q["id"]] = rrf([vector_ranking, keyword_ranking], weights=weights)[:10]

if weights:
    label = f"weighted {weights[0]:.0%} vector / {weights[1]:.0%} BM25"
    name = f"hybrid_w{round(weights[0] * 100)}-{round(weights[1] * 100)}"
else:
    label, name = "equal weights", "hybrid"
summary = summarize(results, questions, exam=exam, method=f"Hybrid ({label}, RRF k=60, top {CANDIDATES} each)")
summary["weights"] = weights
print_report(summary, results, questions, titles)
save(summary, results, name)
