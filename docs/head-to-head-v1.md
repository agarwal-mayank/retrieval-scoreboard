# Head-to-head: vector search vs BM25 (exam v1)

Generated with `scripts/compare_methods.py` from the saved answer sheets of `scripts/run_vector_search.py` (nomic-embed-text, digest 0a109f422b47) and `scripts/run_bm25_search.py`. "Wins" means the method ranked the right article higher; "-" means it wasn't in the top 5.

## Scores

| | hit@5 | hit@1 | MRR |
|---|--:|--:|--:|
| Vector search | 100.0% | 80.0% | 0.874 |
| BM25 | 73.3% | 50.0% | 0.590 |

## Who ranked the right article higher

| Type | Vector wins | BM25 wins | Tie | Both miss |
|------|-----:|-----:|----:|-----:|
| Easy (8) | 0 | 0 | 8 | 0 |
| Paraphrase (12) | 7 | 1 | 4 | 0 |
| Near-twin (6) | 3 | 0 | 3 | 0 |
| Messy (4) | 3 | 0 | 1 | 0 |
| **Overall (30)** | **13** | **1** | **16** | **0** |

## Findings

- **When users use the article's words, the methods tie.** All 8 easy questions were ranked #1 by both. Keyword search is not "worse"; it's literal.
- **The further the wording drifts, the bigger vector search's lead.** Paraphrase: vector won 7, BM25 won 1. Messy: vector won 3 of 4, and BM25 missed the top 5 on 3 of them (MRR 0.125 vs 0.675).
- **BM25 fails loudly when no words overlap.** "My notebook gets really hot and sounds like a jet engine" shares no keywords with "Laptop Overheating and Loud Fan"; BM25's top result was an unrelated security article. "Found a pen drive labeled finance" matched "drive" and returned a shared-drive networking article.
- **BM25's one win was exact phrasing.** Q08 ("mobile data shared to the laptop… never finishes connecting") put the right article #1 under BM25, while vector search ranked a close cousin ("Phone hotspot will not share to laptop") first. Literal matches still help, which is the case for combining both (Level 4: hybrid).
- **Neither method fully handles two-intent questions.** Vector search got both relevant articles into the top 5 for 2 of 2; BM25 for 0 of 2.
- **No question defeated both methods.** The near-misses that remain (vector search: right article at rank 2–5 on 6 questions) are the room hybrid and reranking can work on.

## Caveats

- 30 questions: each one is worth 3.3 points of hit@5, so small differences can be luck. The direction of the gap (consistent across types) matters more than the exact numbers.
- Vector search is at the hit@5 ceiling on this exam. A harder exam v2, written blind, will re-test both methods (#19).
