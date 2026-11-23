# retrieval-scoreboard

Four retrieval methods compete to find the right IT help article. One scoreboard shows who wins, how fast, and at what cost.

> Status: ✅ Level 3 shipped. Vector search beats BM25 on both exams (v2 MRR 0.892 vs 0.723), most of all on real-user wording. Next: Level 4, hybrid + rerank.

## What it is

A small, reproducible benchmark for retrieval-augmented generation (RAG) search. The contestants:

| # | Method | In one line |
|---|--------|-------------|
| 1 | Vector search | Finds articles by meaning, using embeddings |
| 2 | Keyword search (BM25) | Finds articles by matching words |
| 3 | Hybrid | Blends vector and keyword results |
| 4 | Hybrid + rerank | Hybrid, then a reranker reorders the top results |

The arena: 200 synthetic IT help articles and 30 test questions. Each question has one known right answer.

The score: **hit@5**, meaning the share of questions where the right article appears in the top 5 results. Level 5 adds a second score, **faithfulness**: whether each generated answer is actually supported by the articles it cites.

## Why

Most RAG demos skip the question that matters in production: *is the search actually finding the right thing?* This project measures it. It compares methods on the same data with the same test, then adds observability (tracing, latency and cost) so the trade-offs are visible, not guessed.

All data is synthetic. No real company or customer data is used.

## Dataset

### The library: 200 IT help articles

`data/articles.jsonl`, one article per line, 10 categories × 20 articles:

Passwords & sign-in · Multi-factor authentication · VPN & remote access · Email & calendar · Printers & scanning · Laptops & hardware · Wi-Fi & network · Software install & access · Chat & video meetings · Security & phishing

Every article follows the same help-desk structure (Symptoms → Cause → Steps → Still stuck?), runs about 120–220 words, and uses generic names ("the company VPN app", "your email app") rather than real products. Some articles are deliberate **near-twins** ("Battery Drains Too Quickly" vs "Battery Percentage Jumps or Stays Stuck"), so a method has to be precise, not just find "something about batteries".

```json
{"id": "KB0094", "title": "Low toner warning will not clear", "category": "Printers & scanning",
 "body": "Symptoms: The printer shows a low toner message even after you have replaced the cartridge... Cause: ... Steps: 1. ... Still stuck? ..."}
```

**How it was made.** Generated once with Claude Haiku (`claude-haiku-5-5`) by [`scripts/generate_articles.py`](scripts/generate_articles.py), using structured output and a quality gate (exact counts, word limits, no brand names, unique titles across the library). Two batches of 10 per category; the second batch saw the first batch's titles, to avoid repeats and create near-twins. The full recipe (prompts, model, settings, token usage and cost) is in [`data/articles.meta.json`](data/articles.meta.json). One duplicate title was found by the tests and repaired (KB0112); the repair is logged in the same file. Total cost: about US$0.056.

### The exam: 30 questions with a known answer

`data/questions.jsonl` is the golden set: each question names the one article that answers it.

| Type | Count | What it tests |
|------|------:|---------------|
| Easy | 8 | Wording close to the article title |
| Paraphrase | 12 | Same meaning, different words (where keyword search struggles) |
| Near-twin | 6 | Picking the right article over a lookalike |
| Messy | 4 | Real-user wording: vague, two problems in one, typos |

Three questions per category. The messy questions were written by hand from service desk experience; the rest were drafted with Claude and approved by a human reviewer. Questions describing two problems list the second article in `also_relevant`. The exam was written before any search method existed, so it can't be tuned to flatter one approach.

```json
{"id": "Q14", "question": "The battery says 60 percent and a minute later it says 15",
 "answer_article_id": "KB0112", "type": "near-twin"}
```

`data/unanswerable.jsonl` holds questions with **no** matching article. They aren't scored by hit@5. At Level 5, the right behaviour is to say "I don't know" rather than invent an answer.

### The score

[`src/scoreboard/scoring.py`](src/scoreboard/scoring.py) is the referee. Every method hands in a ranked list of article ids per question, and three scores are reported:

- **hit@5**: the share of questions whose right article is in the top 5
- **hit@1**: the share where it's the very first result
- **MRR** (mean reciprocal rank): 1 ÷ the right article's rank (1, ½, ⅓, …; 0 if missing), averaged. Rewards ranking it higher

A random-guess baseline ([`scripts/random_baseline.py`](scripts/random_baseline.py)) sets the floor: 5 picks from 200 articles is about 2.5% expected.

With only 30 questions, each question is worth 3.3 points, so small gaps between methods can be luck. Results are read alongside the per-type breakdown.

## How to run

Needs [uv](https://docs.astral.sh/uv/). uv installs the pinned Python 3.11 and dependencies for you.

```powershell
uv sync                      # install pinned dependencies
copy .env.example .env       # then add your keys (only needed to regenerate the articles)
uv run python -m scoreboard  # run the scoreboard
uv run pytest                # run the tests
uv run python scripts/random_baseline.py   # score the random baseline
```

### Vector search (Level 2)

Runs locally and free with [Ollama](https://ollama.com):

1. Install Ollama and start the app.
2. Pull the embedding model (about 274 MB): `ollama pull nomic-embed-text`
3. Run:

```powershell
uv run python scripts/embed_articles.py       # embed the 200 articles (cached in runs/embeddings/)
uv run python scripts/run_vector_search.py    # score the exam: hit@5, hit@1, MRR, by question type
```

Results above used `nomic-embed-text` with digest `0a109f422b47`. Articles are embedded as title + body with the `search_document: ` prefix, questions with `search_query: `.

### Keyword search (Level 3)

No Ollama or API key needed:

```powershell
uv run python scripts/run_bm25_search.py      # BM25 on the exam: hit@5, hit@1, MRR, by question type (add --exam v2 for exam v2)
uv run python scripts/compare_methods.py runs/results/vector_nomic-embed-text_0a109f422b47_v1.json runs/results/bm25_v1.json
```

BM25 uses the standard [rank-bm25](https://pypi.org/project/rank-bm25/) implementation (`BM25Okapi`, default settings) over title + body, with our own tokenizer: lowercase, punctuation splits words, common stop words dropped.

### Regenerating the data

The article library is already committed. To regenerate it (needs `ANTHROPIC_API_KEY` in `.env`; costs a few cents):

```powershell
uv run --env-file .env python scripts/generate_articles.py
```

## Results

_Two exams: v1 (30 questions) and v2 (60 fresh questions on randomly picked articles, frozen before any method ran). Strict marking: only the listed article counts. Filled in as each level ships. Latency and cost arrive with Level 6._

| Method | v1 hit@5 | v1 hit@1 | v1 MRR | v2 hit@5 | v2 hit@1 | v2 MRR | Cost per 1k queries |
|--------|------:|------:|----:|------:|------:|----:|--------------------:|
| Random (floor baseline, seed 42) | 0.0% | 0.0% | 0.000 | – | – | – | – |
| Vector (nomic-embed-text, local) | 100.0% | 80.0% | 0.874 | 98.3% | 83.3% | 0.892 | $0 (runs locally) |
| Keyword (BM25) | 73.3% | 50.0% | 0.590 | 85.0% | 63.3% | 0.723 | $0 (runs locally) |
| Hybrid | – | – | – | – | – | – | – |
| Hybrid + rerank | – | – | – | – | – | – | – |

Exam v2 details, lenient marking and findings: [docs/exam-v2-results.md](docs/exam-v2-results.md). The v1 results by type follow.

**By question type, exam v1 (MRR)**

| Type | n | Vector | BM25 |
|------|--:|-------:|-----:|
| Easy | 8 | 1.000 | 1.000 |
| Paraphrase | 12 | 0.903 | 0.496 |
| Near-twin | 6 | 0.783 | 0.542 |
| Messy | 4 | 0.675 | 0.125 |

**Reading it.**

- When questions use the article's own words, the two methods tie: both put all 8 easy questions first.
- The further the wording drifts, the bigger vector search's lead. On messy, real-user questions BM25 missed the top 5 for 3 of 4.
- Question by question, vector search ranked the right article higher 13 times, BM25 once, and they tied 16 times; no question beat both. Full head-to-head: [docs/head-to-head-v1.md](docs/head-to-head-v1.md).
- Vector search is at the hit@5 ceiling on v1, so hit@1 and MRR carry the comparison. The exam was not edited after seeing results.
- **Exam v2 confirmed it on fresh, randomly chosen ground:** vector search leads again (MRR 0.892 vs 0.723), with the widest gap again on real-user, messy wording (0.801 vs 0.456). Next test: a library about 30 times larger, from real data (#30).

## Roadmap

- [x] **Level 1: Build the library.** 200 synthetic articles, a 30-question test set, the hit@5 scorer and a random baseline
- [x] **Level 2: Meaning search.** Vector search with local embeddings (nomic-embed-text via Ollama), cosine similarity, hit@1 and MRR
- [x] **Level 3: Keyword search.** BM25 with our own tokenizer, a question-by-question head-to-head, and a harder exam v2 to re-test both methods
- [ ] **Level 4: Boss fight.** Hybrid and hybrid + rerank
- [ ] **Level 5: Answer and cite.** Generate an answer from the retrieved articles, cite the sources, and score whether each answer is supported by what was retrieved (faithfulness)
- [ ] **Level 6: X-ray vision.** Observability with tracing, latency and cost
- [ ] **Level 7: Ship it.** Polish, write-up and final results

## Licence

[MIT](LICENSE)
