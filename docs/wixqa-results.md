# Real-world round: WixQA

Does the scoreboard's ranking of methods hold on a larger, real dataset? WixQA (Wix.com AI Research, MIT licence) has 6,221 real help-centre articles and two sets of human questions:

- **ExpertWritten** (200): authentic customer support tickets, with step-by-step answers drafted and triple-reviewed by Wix support experts.
- **Simulated** (200): user–expert support chats, distilled into a single question and answer by GPT-4o, then filtered and reviewed by experts.

Each question names 1–3 correct articles (98 of the 400 have more than one). A third set of 6,221 GPT-4o-generated questions was not used, so that no model-written exam is involved. The data was downloaded from the Hugging Face dataset `Wix/WixQA` and is kept out of this repo.

## Results (400 questions)

"Lenient" = any of the question's correct articles counts (the headline here, since many questions have several). "Strict" = only the first listed article counts.

| Method | Lenient hit@5 | Lenient hit@1 | Lenient MRR | Strict hit@5 | Strict MRR | nDCG@10 |
|---|--:|--:|--:|--:|--:|--:|
| **Hybrid 70/30 + rerank (Claude Haiku)** | **80.2%** | 56.0% | **0.661** | **74.0%** | **0.602** | **0.664** |
| Vector + rerank (Claude Haiku) | 76.8% | **57.0%** | 0.653 | 71.5% | 0.596 | 0.647 |
| Vector + rerank (qwen2.5:7b, local) | 72.2% | 45.2% | 0.559 | 67.0% | 0.510 | 0.583 |
| Hybrid, 70% vector / 30% BM25 | 70.0% | 34.5% | 0.481 | 64.8% | 0.438 | 0.545 |
| Hybrid, equal weights | 68.0% | 35.0% | 0.472 | 63.5% | 0.432 | 0.541 |
| Vector (nomic-embed-text, local) | 66.8% | 31.2% | 0.441 | 61.0% | 0.403 | 0.507 |
| BM25 | 52.0% | 23.5% | 0.340 | 48.0% | 0.308 | 0.395 |

Both rerankers re-order vector search's top 10, with each article trimmed to its first 400 words. Haiku: 1.5 seconds per question, US$0.249 for the 400 questions (2.08M input and 82k output tokens), 0 unreadable replies. qwen: 4.8 seconds per question, free, 0 unreadable replies.

An earlier run a day before reported vector search at 31.5% hit@1 and MRR 0.443 (hybrid equal: 35.2%, 0.473). The rankings for a question or two changed between the two days: embedding the same questions twice within one session gives identical numbers and rankings, so the likely cause is tiny numeric differences after Ollama reloaded the model. BM25, which doesn't use embeddings, didn't change. All tables here use the latest run, which every reranker was also built on.

**By question set (lenient MRR / nDCG@10)**

| Method | ExpertWritten (200) | Simulated (200) |
|---|---|---|
| Hybrid 70/30 + rerank (Haiku) | 0.694 / 0.680 | 0.628 / 0.647 |
| Vector + rerank (Haiku) | 0.694 / 0.675 | 0.612 / 0.620 |
| Vector + rerank (qwen) | 0.594 / 0.608 | 0.524 / 0.559 |
| Hybrid 70/30 | 0.512 / 0.566 | 0.450 / 0.524 |
| Vector | 0.479 / 0.534 | 0.404 / 0.479 |

## Does a better shortlist help the reranker?

A top-10 reranker can only reorder what's in its shortlist, so hit@10 is its ceiling:

| Shortlist | hit@10 | ExpertWritten | Simulated |
|---|--:|--:|--:|
| Hybrid 70/30 | 80.5% | 84.5% | 76.5% |
| Vector | 77.0% | 81.5% | 72.5% |

Reranking the hybrid shortlist with Haiku (one run, US$0.2625, 1.5 seconds per question, 0 unreadable replies) against reranking the vector shortlist:

- **More right articles found:** hit@5 76.8% → 80.2%, Recall@5 0.715 → 0.747, nDCG@10 0.647 → 0.664. That's about the 3.5-point higher ceiling, carried through.
- **No gain at #1:** hit@1 57.0% → 56.0% (4 questions), MRR 0.653 → 0.661. Within noise.
- **The gain is on chat-style questions:** Simulated MRR 0.612 → 0.628 and nDCG@10 0.620 → 0.647; ExpertWritten MRR is unchanged at 0.694.

So a better shortlist helps the reranker find more right articles, but on this data it barely changes which article comes first. The reranker itself is still the bigger lever (vector 0.441 → 0.653 MRR from reranking, against 0.653 → 0.661 from the better shortlist).

## Findings

- **Reranking is the biggest win on real data too.** Haiku reranking lifts hit@1 from 31.2% to 57.0% and MRR from 0.441 to 0.653, far ahead of any hybrid. The free local qwen reranker also beats every non-reranked method (MRR 0.559). Reranking the hybrid shortlist instead (see above) adds a little more, mostly in how many right articles reach the top 5.
- **On real data, hybrid beats vector search alone**, the opposite of the synthetic exams. The 70/30 weighting, chosen before any run, scored best of the non-reranked methods (MRR 0.481 vs 0.441). The best method depends on the data, so evaluate on data that looks like yours.
- **Real data is much harder:** MRR is about half of the synthetic exams' (0.44–0.48 vs about 0.9). 6,221 articles means far more lookalikes competing for the top 5.
- **Chat-style questions are harder than tickets for every method**, and that's where hybrid helps most (vector 59.5% → 66.5% hit@5). Likely reasons: Simulated questions are shorter (median 12 words vs 18, so fewer clues to match), and fewer of them have several correct articles (27 vs 52), which under lenient marking means fewer ways to score a hit.

## Compared with the WixQA paper

The paper (Cohen et al., 2025, [arXiv:2505.08643](https://arxiv.org/abs/2505.08643), Tables 3–4) reports **context recall**, an LLM-judged measure of whether the retrieved text covers the expert answer, with BM25 and E5 retrieval:

| | ExpertWritten | Simulated |
|---|--:|--:|
| BM25 | 0.72–0.73 | 0.55 |
| E5 | 0.81 | 0.67 |

(The ranges cover the four answer-generation models in the tables.)

- **Same pattern as ours:** dense retrieval beats BM25 on both sets, and ExpertWritten scores higher than Simulated for both methods.
- **Different metric:** context recall is judged by an LLM against the expert answer, while our scores check whether the exact listed article was retrieved, using different models. The numbers are not directly comparable.

## Attribution

WixQA by Wix.com AI Research, released under the MIT Licence: https://huggingface.co/datasets/Wix/WixQA. Paper: Cohen et al., "WixQA: A Multi-Dataset Benchmark for Enterprise Retrieval-Augmented Generation", 2025, arXiv:2505.08643, DOI 10.57967/hf/8725.
