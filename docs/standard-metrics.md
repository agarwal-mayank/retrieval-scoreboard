# Standard retrieval metrics: Recall@5 and nDCG@10

The field's usual retrieval metrics, added alongside hit@5, hit@1 and MRR. Both count **every** correct article for a question (the answer plus any `also_relevant` twins), so they handle WixQA's questions with 1–3 correct articles naturally.

- **Recall@5**: the share of a question's correct articles that appear in the top 5, averaged over questions. With one correct article it equals hit@5.
- **nDCG@10**: each correct article in the top 10 earns 1 ÷ log₂(rank + 1) (#1 = 1.0, #2 = 0.63, #3 = 0.5, #10 = 0.29); the sum is divided by the best possible score for that question, so it runs from 0 to 1. It's the headline metric of the BEIR and MTEB retrieval benchmarks. `ndcg_at_k` was written by Mayank, test-first.

All scores come from the saved top-10 rankings (`scripts/rescore_results.py`); nothing was re-searched, and no API was used.

| Method | v1 Recall@5 | v1 nDCG@10 | v2 Recall@5 | v2 nDCG@10 | WixQA Recall@5 | WixQA nDCG@10 |
|---|--:|--:|--:|--:|--:|--:|
| Vector + rerank (qwen2.5:7b) | 0.950 | 0.934 | 0.961 | **0.967** | not run | not run |
| Vector (nomic-embed-text) | **1.000** | 0.914 | 0.950 | 0.947 | 0.610 | 0.507 |
| Hybrid, 70% vector / 30% BM25 | 0.917 | 0.850 | 0.903 | 0.912 | **0.647** | **0.544** |
| Hybrid, equal weights | 0.917 | 0.842 | 0.900 | 0.886 | 0.628 | 0.542 |
| BM25 | 0.733 | 0.677 | 0.808 | 0.770 | 0.474 | 0.395 |

## Findings

- **The standard metrics tell the same story as hit@5 and MRR.** On the synthetic exams, reranking leads and vector search beats hybrid. On WixQA, the 70/30 hybrid leads (nDCG@10 0.544 vs vector's 0.507), and BM25 is last everywhere.
- **nDCG@10 sits between hit@5 and MRR**, as expected: it rewards rank like MRR, but also credits correct articles found at positions 6–10 and every correct article, not just the first.
- **Reranking scores the highest nDCG@10 of any method** (v2: 0.967), confirming that its gains are about putting the right articles at the very top.
- On v1, vector search finds every correct article in the top 5 (Recall@5 1.000), but reranking ranks more of them first (hit@1 86.7% vs 80.0%); the two metrics capture different strengths.

## Caveats

- Relevance is binary (right or not), not graded; nDCG supports grades, but our answer keys don't have them.
- WixQA reranking is built but not run yet, so it has no row.
