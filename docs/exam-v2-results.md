# Exam v2 results: vector search vs BM25

Exam v2 has 60 questions on articles picked at random by a fixed seed (6 per category, none reused from v1), with a harder mix: 6 easy, 18 paraphrase, 18 near-twin, 18 messy. The 18 messy questions were written by Mayank. The exam was committed before either method ran on it.

## Scores (strict: only the listed article counts)

| | v1 hit@5 | v1 hit@1 | v1 MRR | v2 hit@5 | v2 hit@1 | v2 MRR |
|---|--:|--:|--:|--:|--:|--:|
| Vector search (nomic-embed-text) | 100.0% | 80.0% | 0.874 | 98.3% | 83.3% | 0.892 |
| BM25 | 73.3% | 50.0% | 0.590 | 85.0% | 63.3% | 0.723 |

**By type (v2, MRR)**

| Type | n | Vector | BM25 |
|------|--:|-------:|-----:|
| Easy | 6 | 1.000 | 1.000 |
| Paraphrase | 18 | 0.866 | 0.713 |
| Near-twin | 18 | 0.972 | 0.907 |
| Messy | 18 | 0.801 | 0.456 |

**Lenient marking** (a genuine twin article in another category also counts): vector 98.3% / 91.7% / 0.943, BM25 86.7% / 68.3% / 0.759.

## Who ranked the right article higher (v2)

| Type | Vector wins | BM25 wins | Tie | Both miss |
|------|-----:|-----:|----:|-----:|
| Easy (6) | 0 | 0 | 6 | 0 |
| Paraphrase (18) | 6 | 3 | 9 | 0 |
| Near-twin (18) | 3 | 1 | 14 | 0 |
| Messy (18) | 12 | 2 | 4 | 0 |
| **Overall (60)** | **21** | **6** | **33** | **0** |

## Findings

- **The v1 conclusion holds on fresh, randomly chosen ground.** Vector search leads BM25 again on every measure (MRR 0.892 vs 0.723), and the gap is again widest on real-user wording: messy MRR 0.801 vs 0.456, with vector search winning 12 of 18 messy questions.
- **Messy questions are the hardest for both methods.** Vector search's only miss from the top 5 was a messy question (V38: a text saying "your account is locked" while sign-in still works; vector search's top result was a sign-in article, not the phishing-text article).
- **BM25 scored higher on v2 than on v1** (MRR 0.590 → 0.723), mainly because v2's near-twin questions carry distinctive words ("conference room", "read-only", "black screen"). Word-matching rewards specific vocabulary.
- **Duplicate articles cost points.** Counting twin articles as acceptable lifts vector search's hit@1 from 83.3% to 91.7%: about 1 in 12 of its "wrong" first results was an equally valid twin from another category. Merging those duplicates (#10) would make the library, and the scoreboard, cleaner.
- **The hit@5 ceiling is still there for vector search** (98.3%). A 200-article library is too small to separate strong methods on hit@5; the real-world round on a library about 30 times larger (#30) is the next test of whether the ranking holds.

## Caveats

- 60 questions: each is worth about 1.7 points of hit@5. The direction and consistency of the gap matter more than exact numbers.
- Near-twin questions were written to point at one article over its lookalike, which also helps keyword search when the distinguishing words are literal.
