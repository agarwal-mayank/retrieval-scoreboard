# retrieval-scoreboard

Four retrieval methods compete to find the right IT help article. One scoreboard shows who wins, how fast, and at what cost.

> Status: 🚧 Level 0 (set-up). Results land as each level ships.

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

## How to run

_Coming in Level 1._ Planned shape:

```powershell
uv sync                    # install pinned dependencies
copy .env.example .env     # then add your keys
uv run python -m scoreboard  # run all methods and print the scoreboard
```

## Results

_Placeholder: filled in as each level ships._

| Method | hit@5 | Avg latency (ms) | Cost per 1k queries |
|--------|------:|-----------------:|--------------------:|
| Vector | – | – | – |
| Keyword (BM25) | – | – | – |
| Hybrid | – | – | – |
| Hybrid + rerank | – | – | – |

## Roadmap

- [ ] **Level 1: Build the library.** Generate 200 synthetic articles and a 30-question test set
- [ ] **Level 2: Meaning search.** Vector search with embeddings
- [ ] **Level 3: Keyword search.** BM25
- [ ] **Level 4: Boss fight.** Hybrid and hybrid + rerank
- [ ] **Level 5: Answer and cite.** Generate an answer from the retrieved articles, cite the sources, and score whether each answer is supported by what was retrieved (faithfulness)
- [ ] **Level 6: X-ray vision.** Observability with tracing, latency and cost
- [ ] **Level 7: Ship it.** Polish, write-up and final results

## Licence

[MIT](LICENSE)
