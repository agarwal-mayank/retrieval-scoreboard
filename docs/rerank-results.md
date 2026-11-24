# Rerank results: does a second judge improve vector search?

Vector search finds the top 10 candidates; a local chat model, qwen2.5:7b in Ollama (Q4_K_M, digest 845dbda0ea48, temperature 0), reads the question with all 10 (title + body) and lists them in order. The new top 5 are scored. This is "listwise" reranking with a general LLM, not a dedicated reranker model. Each exam was run once.

## Scores

| | v1 hit@5 | v1 hit@1 | v1 MRR | v2 hit@5 | v2 hit@1 | v2 MRR | v2 lenient hit@1 |
|---|--:|--:|--:|--:|--:|--:|--:|
| **Vector + rerank (qwen2.5:7b)** | 96.7% | **86.7%** | **0.917** | 98.3% | **90.0%** | **0.938** | **96.7%** |
| Vector alone | 100.0% | 80.0% | 0.874 | 98.3% | 83.3% | 0.892 | 91.7% |
| Hybrid, 70/30 | 93.3% | 70.0% | 0.786 | 91.7% | 78.3% | 0.847 | 85.0% |
| BM25 alone | 73.3% | 50.0% | 0.590 | 85.0% | 63.3% | 0.723 | 68.3% |

**By type, exam v2 (MRR)**

| Type | Vector + rerank | Vector alone |
|------|------:|------:|
| Easy | 1.000 | 1.000 |
| Paraphrase | 0.944 | 0.866 |
| Near-twin | 0.972 | 0.972 |
| Messy | 0.875 | 0.801 |

Cost and speed: about 4 seconds per question on Mayank's PC (3.9s on v1, 4.2s on v2), $0, fully local. qwen's reply could be read every time (0 fallbacks out of 90).

## Head-to-head against vector alone

| | Rerank wins | Vector wins | Tie | Both miss |
|---|--:|--:|--:|--:|
| Exam v1 | 4 | 3 | 23 | 0 |
| Exam v2 | 6 | 1 | 52 | 1 |

## Findings

- **Reranking is the first thing to beat vector search alone.** On v2: hit@1 83.3% → 90.0%, MRR 0.892 → 0.938. On v1: hit@1 80.0% → 86.7%, MRR 0.874 → 0.917.
- **The biggest gains are where vector search was weakest.** v2 paraphrase MRR 0.866 → 0.944 and messy 0.801 → 0.875; v1 messy questions went from 0.675 to a perfect 1.000 (only 4 questions, so treat with care). Reading the full articles helps with real-user wording.
- **It isn't free of mistakes.** On v1, two near-twin questions got worse (MRR 0.783 → 0.667), and one (Q07, VPN dropping after sleep) was pushed out of the top 5 entirely, so v1 hit@5 fell from 100% to 96.7%. A small model can be fooled by a lookalike that shares surface details.
- **With twins allowed (lenient), the reranked first answer is right 96.7% of the time on v2.** Most remaining "misses" at #1 are equally valid duplicate articles from other categories (e.g. the authenticator-code family), which strengthens the case for #10.
- **The trade-off is time.** About 4 extra seconds per question for a 5–7 point gain in hit@1. Level 6 will track this properly.

## Caveats

- 30 + 60 questions; small per-type groups (v1 has only 4 messy and 6 near-twin questions).
- One model, one prompt, one run each, all decided before running. No prompt tuning was done on these exams.
- A general 7B chat model, not a trained reranker. Dedicated rerankers or a larger model might do better; that's a possible extra contestant.
