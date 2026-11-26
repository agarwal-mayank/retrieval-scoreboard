# Real-world round: WixQA

Does the scoreboard's ranking of methods hold on a larger, real dataset? WixQA (Wix.com AI Research, MIT licence) has 6,221 real help-centre articles and two sets of human questions:

- **ExpertWritten** (200): authentic customer support tickets, with step-by-step answers drafted and triple-reviewed by Wix support experts.
- **Simulated** (200): user–expert support chats, distilled into a single question and answer by GPT-4o, then filtered and reviewed by experts.

Each question names 1–3 correct articles (98 of the 400 have more than one). A third set of 6,221 GPT-4o-generated questions was not used, so that no model-written exam is involved. The data was downloaded from the Hugging Face dataset `Wix/WixQA` and is kept out of this repo.

## Results (400 questions)

"Lenient" = any of the question's correct articles counts (the headline here, since many questions have several). "Strict" = only the first listed article counts.

| Method | Lenient hit@5 | Lenient hit@1 | Lenient MRR | Strict hit@5 | Strict MRR |
|---|--:|--:|--:|--:|--:|
| **Hybrid, 70% vector / 30% BM25** | **70.0%** | 34.5% | **0.481** | **64.8%** | **0.437** |
| Hybrid, equal weights | 68.0% | **35.2%** | 0.473 | 63.5% | 0.432 |
| Vector (nomic-embed-text, local) | 66.8% | 31.5% | 0.443 | 61.0% | 0.403 |
| BM25 | 52.0% | 23.5% | 0.340 | 48.0% | 0.308 |

**By question set (lenient hit@5 / hit@1 / MRR)**

| Method | ExpertWritten (200) | Simulated (200) |
|---|---|---|
| Hybrid 70/30 | 75.0% / 37.0% / 0.515 | 65.0% / 32.0% / 0.447 |
| Hybrid equal | 69.5% / 37.0% / 0.493 | 66.5% / 33.5% / 0.452 |
| Vector | 74.0% / 34.5% / 0.481 | 59.5% / 28.5% / 0.404 |
| BM25 | 56.0% / 27.0% / 0.378 | 48.0% / 20.0% / 0.301 |

## Findings

- **On real data, hybrid beats vector search alone**, the opposite of the synthetic exams. The 70/30 weighting, chosen before any run, scored best (MRR 0.481 vs 0.443). The best method depends on the data, so evaluate on data that looks like yours.
- **Real data is much harder:** MRR is about half of the synthetic exams' (0.44–0.48 vs about 0.9). 6,221 articles means far more lookalikes competing for the top 5.
- **Chat-style questions are harder than tickets for every method**, and that's where hybrid helps most (vector 59.5% → 66.5% hit@5). Likely reasons: Simulated questions are shorter (median 12 words vs 18, so fewer clues to match), and fewer of them have several correct articles (27 vs 52), which under lenient marking means fewer ways to score a hit.

## Compared with the WixQA paper

The paper (Cohen et al., 2025, [arXiv:2505.08643](https://arxiv.org/abs/2505.08643), Tables 3–4) reports **context recall**, an LLM-judged measure of whether the retrieved text covers the expert answer, with BM25 and E5 retrieval:

| | ExpertWritten | Simulated |
|---|--:|--:|
| BM25 | 0.55 | 0.95–0.96 |
| E5 | 0.67 | 0.96–0.97 |

(The ranges cover the four answer-generation models in the tables.)

- **Same pattern on embeddings vs BM25:** dense retrieval beats BM25 in both, most clearly on ExpertWritten.
- **Different metric, different picture on the two sets:** under the paper's context recall, Simulated scores *higher* than ExpertWritten; under our exact-article MRR it scores lower. Simulated answers are short, so the retrieved text more easily "covers" them even when the exact listed article isn't found. The numbers measure different things and are not directly comparable.

## Not done yet

- Reranking on WixQA (Claude Haiku and local qwen2.5) is built and tested (`scripts/run_wixqa.py`) but not run yet.

## Attribution

WixQA by Wix.com AI Research, released under the MIT Licence: https://huggingface.co/datasets/Wix/WixQA. Paper: Cohen et al., "WixQA: A Multi-Dataset Benchmark for Enterprise Retrieval-Augmented Generation", 2025, arXiv:2505.08643, DOI 10.57967/hf/8725.
