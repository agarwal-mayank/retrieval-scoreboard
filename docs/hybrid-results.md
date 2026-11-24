# Hybrid search results: does combining vector search and BM25 help?

Hybrid search merges each method's top 20 with Reciprocal Rank Fusion (RRF, k = 60) and keeps the top 5. Two versions were run once each on both exams:

- **Equal weights**: the textbook default.
- **Weighted 70% vector / 30% BM25**: weights chosen by Mayank before any weighted run, not searched for, so they weren't tuned to the exams.

## Scores (strict marking)

| | v1 hit@5 | v1 hit@1 | v1 MRR | v2 hit@5 | v2 hit@1 | v2 MRR |
|---|--:|--:|--:|--:|--:|--:|
| Vector alone | 100.0% | 80.0% | 0.874 | 98.3% | 83.3% | 0.892 |
| Hybrid, weighted 70/30 | 93.3% | 70.0% | 0.786 | 91.7% | 78.3% | 0.847 |
| Hybrid, equal weights | 93.3% | 70.0% | 0.776 | 91.7% | 76.7% | 0.835 |
| BM25 alone | 73.3% | 50.0% | 0.590 | 85.0% | 63.3% | 0.723 |

**By type, exam v2 (MRR)**

| Type | Vector | Hybrid 70/30 | Hybrid equal | BM25 |
|------|-------:|-------------:|-------------:|-----:|
| Easy | 1.000 | 1.000 | 1.000 | 1.000 |
| Paraphrase | 0.866 | 0.833 | 0.819 | 0.713 |
| Near-twin | 0.972 | 0.972 | 1.000 | 0.907 |
| Messy | 0.801 | 0.685 | 0.630 | 0.456 |

## Head-to-head against vector alone

| | v1 hybrid wins | v1 vector wins | v2 hybrid wins | v2 vector wins |
|---|--:|--:|--:|--:|
| Equal weights | 2 | 5 | 5 | 11 |
| Weighted 70/30 | 1 | 5 | 4 | 8 |

## Findings

- **Hybrid did not beat vector search alone on either exam.** Combining with a much weaker method cost more than it gained: v2 MRR 0.835 (equal) and 0.847 (70/30) against 0.892.
- **The damage is on messy, real-user wording.** When BM25 fails completely, it still hands in 20 guesses, and RRF gives each one a vote. Those votes push vector search's correct answer down. Example: V42 "multiple password reset emails": vector search had the right article at #1, BM25 didn't have it in its top 5, and hybrid dropped it to #2.
- **Hybrid helped where keyword search is strong.** On v2's near-twin questions, which carry distinctive words, equal-weight hybrid reached a perfect 1.000 MRR.
- **Weighting vector search at 70% helped, but only a little** (v2 MRR 0.835 → 0.847). With k = 60, RRF votes are very flat (1/61 for rank 1 vs 1/80 for rank 20), so being in both lists matters more than the weight. Lowering k or fusing actual scores instead of ranks are possible next experiments, to be chosen on v1 and judged on v2.
- **"Hybrid always wins" is not a law.** It depends on both methods being reasonably good on the same questions. On this data, vector search alone is the stronger default.

## Caveats

- 30 + 60 questions; each v2 question is worth about 1.7 points of hit@5.
- Only two weightings were tried, both decided before running. Searching for the best weight on these exams would be tuning to the test.
