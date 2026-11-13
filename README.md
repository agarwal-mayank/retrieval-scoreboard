# retrieval-scoreboard

Four retrieval methods compete to find the right IT help article. One scoreboard shows who wins, how fast, and at what cost.

> Status: ✅ Level 1 shipped (dataset, test set, scorer, random baseline). Next: Level 2, meaning search.

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

[`src/scoreboard/scoring.py`](src/scoreboard/scoring.py) is the referee. Every method hands in a ranked list of article ids per question, and **hit@5** is the share of questions whose right article is in the top 5. A random-guess baseline ([`scripts/random_baseline.py`](scripts/random_baseline.py)) sets the floor: 5 picks from 200 articles is about 2.5% expected.

With only 30 questions, each question is worth 3.3 points, so small gaps between methods can be luck. Results are read alongside the per-type breakdown.

## How to run

Needs [uv](https://docs.astral.sh/uv/). uv installs the pinned Python 3.11 and dependencies for you.

```powershell
uv sync                      # install pinned dependencies
copy .env.example .env       # then add your keys (needed from Level 2)
uv run python -m scoreboard  # run the scoreboard
uv run pytest                # run the tests
uv run python scripts/random_baseline.py   # score the random baseline
```

The article library is already committed. To regenerate it (needs `ANTHROPIC_API_KEY` in `.env`; costs a few cents):

```powershell
uv run --env-file .env python scripts/generate_articles.py
```

## Results

_Filled in as each level ships._

| Method | hit@5 | Avg latency (ms) | Cost per 1k queries |
|--------|------:|-----------------:|--------------------:|
| Random (floor baseline) | 0.0% (0/30, seed 42; ~2.5% expected) | – | – |
| Vector | – | – | – |
| Keyword (BM25) | – | – | – |
| Hybrid | – | – | – |
| Hybrid + rerank | – | – | – |

## Roadmap

- [x] **Level 1: Build the library.** 200 synthetic articles, a 30-question test set, the hit@5 scorer and a random baseline
- [ ] **Level 2: Meaning search.** Vector search with embeddings
- [ ] **Level 3: Keyword search.** BM25
- [ ] **Level 4: Boss fight.** Hybrid and hybrid + rerank
- [ ] **Level 5: Answer and cite.** Generate an answer from the retrieved articles, cite the sources, and score whether each answer is supported by what was retrieved (faithfulness)
- [ ] **Level 6: X-ray vision.** Observability with tracing, latency and cost
- [ ] **Level 7: Ship it.** Polish, write-up and final results

## Licence

[MIT](LICENSE)
