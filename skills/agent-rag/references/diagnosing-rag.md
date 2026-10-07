# Diagnosing RAG

The stage list matches the `rag-diagnostician` subagent.

## Log enough to diagnose

Per query:

- Original query, rewritten queries, extracted filters.
- Candidate chunk IDs with dense, BM25 and fused scores, before reranking.
- Reranker scores and final chunk IDs passed to the model, in order.
- Assembled prompt (or a reference), answer, cited IDs.
- Index version: parser, chunker settings, embedding model + version.

If retrieval isn't logged, logging it is the first fix (`agent-observability`: retrieval
spans with `gen_ai.retrieval.documents` or OpenInference `retrieval.documents.*`).

## Stop at the first stage that lost the answer

For each failing question, find where the answer lives in the corpus (grep it if local),
walk the stages in order, and record only the **first** failing stage; later ones cascade.

| # | Stage | Check | Fix |
|---|---|---|---|
| 1 | Corpus | Is the answer in the source at all? Current version? | Add or refresh the source |
| 2 | Ingestion / chunking | Survived parsing (tables, PDFs, headers)? Split across chunks or stripped of findable context? | Parser; structure-aware chunking; chunk headers |
| 3 | Retrieval | In the top candidate k? Try the literal query and a keyword search; try exact vector search | Keyword-only hit → hybrid. Neither → rewriting, contextual retrieval, question-aligned chunks, missing filter. Exact hits but ANN misses → index params (`vector-indexes.md`) |
| 4 | Ranking / filtering | Ranked below the cut, or removed by a filter? Or a constraint-breaking result ranked in? | Reranker; candidate and final k; fix the filter; move constraints into filters |
| 5 | Context assembly | In the prompt but buried mid-context, truncated, duplicated or contradicted? Across traces: citations cluster at first/last slots, never the middle → position bias | Best at the edges; dedup; fewer chunks; resolve version conflicts |
| 6 | Generation | Right chunk clearly in context, answer still wrong or unfaithful? | Answer only from context, quote-first, allow "I don't know", require citations; then model |

At stage 6, a faithful but unhelpful answer is an answerability failure: decide with the
user whether to abstain, clarify or escalate, and add unanswerable queries to the set.

## User complaints → first guess

| Users say | Likely cause | Stage |
|---|---|---|
| "Close, but missed a key detail" | Exception or condition lost at a chunk boundary | 2 |
| "Gave me a table, no idea what it means" | Table chunked without its title or explanation | 2 |
| "It contradicted itself" | Conflicting chunks without version metadata | 2 / 5 |
| "Couldn't find something I know is there" | Bad boundaries, or a filter dropped it | 2 / 4 |
| "I said not black / under $200 and got the opposite" | Constraint left to similarity | 4 |

## Tally, then fix in order

```
Stage tally (n = 40 failing questions)
corpus 3 (8%) | ingestion 11 (28%) | retrieval 14 (35%) | ranking 5 (12%) | assembly 2 (5%) | generation 5 (12%)
```

- Fix the largest stage first. Rank fixes by impact ÷ effort; attach to each the metric that
  will show it worked (recall@k at candidate k, at final k, faithfulness pass rate).
- **Fix order:** (1) preprocessing and contextual chunking, usually the biggest gain;
  (2) BM25 hybrid and reranking on the existing search; (3) filters, query rewriting,
  routing; (4) graph, multi-representation and other heavy techniques only for what still
  fails. New embedder, vector DB or framework only when retrieval dominates and cheap fixes
  are measured.
- Don't tune generation before retrieval is validated; the fix regresses when the query mix
  shifts.
- Log each change in `experiment-log.md` with metric delta, added latency and cost.

## Weak query clusters and the flywheel

- Log mean similarity and top reranker score per query; low scorers cluster into topics the
  index covers badly.
- Cluster real queries by topic and needed capability (tables, comparisons, "latest").
  Compute recall and failure rate per cluster; fix the worst high-volume cluster first.
- Loop: baseline (hybrid + rerank) → synthetic questions per chunk, realism-filtered → fast
  recall@k/MRR on every change → collect real queries and feedback → cluster → one targeted
  fix for the worst cluster → monitor → fold failures into the labelled set → repeat.
