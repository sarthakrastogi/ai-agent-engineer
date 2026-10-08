# Retrieval and ranking

## Embeddings

- Shortlist from a retrieval leaderboard (e.g. MTEB's retrieval tab), weighing dimensions,
  storage, latency, price, languages and max input length. Then **test 2–3 candidates plus
  BM25 on your labelled set**; BM25 is a strong zero-shot baseline and dense models often
  underperform out of domain. Which wins depends on the corpus.
- **Changing the embedder means a full re-index.** Never mix two models' vectors in one
  index. Record model + version in index metadata and on retrieval spans.
- Fine-tune an embedder on query → chunk pairs only after hybrid, reranking and chunk
  context are in place and measured.

## Hybrid BM25 + dense

- **Default to hybrid.** BM25 catches IDs, SKUs, error codes, product names, jargon,
  misspellings; dense catches paraphrase.
- **Fusion:** Reciprocal Rank Fusion, score = Σ 1/(60 + rank), needs no score calibration.
  Weighted score fusion (`alpha` 0 = BM25 … 1 = dense) must be tuned on the labelled set.
- Keep both indexes in one store where possible so the same filters apply and they don't
  drift; otherwise query both and fuse in code.
- With a reranker downstream, tune the first stage for recall, not order: over-fetch.

## Vector index (ANN)

- ANN is one more recall loss, below the embedder. **On labelled queries, compare the
  index's top-k with exact search** over the same vectors; if exact finds the gold chunk and
  the index doesn't, tune the index before touching the embedder or chunking. Re-check after
  changing index parameters.
- What counts is **recall at the candidate k**: a reranker can't recover a chunk the index
  never returned. Keep `ef_search` ≥ candidate k.
- Small corpora don't need ANN: exact search or a vector column in your existing database.
- Pick the recall you need, then the cheapest setting that reaches it (95% recall can be
  ~10× faster than 99%). Sweep `ef_search` against p95 latency; never keep defaults
  unmeasured. Frequent re-indexing can make HNSW build time dominate; consider IVF.
- **Filtered search** (tenant, ACL, date) can be 10–100× slower: the search visits many
  nodes to find a few that pass. Use native pre-filtering, partitions per high-cardinality
  value (per tenant), or for very selective filters filter in a database and search the
  survivors exactly. Benchmark at realistic selectivity; ACL filters are mandatory, so their
  latency is part of the budget.
- **Not OLTP.** Deletes are tombstones, updates are delete + insert; churn degrades graph
  connectivity. Batch updates, re-index periodically, track recall after heavy churn.
- Fan-out to all shards means the slowest sets p99; routed shards are faster but can miss
  neighbours. Warm HNSW into memory after deploys and restarts.
- Use PQ or fewer dimensions only after measuring the recall cost.

## Reranking

- **Two stages:** retrieve broadly (top ~25–150), rerank with a cross-encoder to the final
  k (3–20). Rerank only the shortlist; cross-encoders are too slow for the corpus.
- Tune final k on your set: top-20 after reranking often beats top-5/10, but more chunks add
  distraction and tokens.
- Late-interaction (ColBERT-style) models are near cross-encoder quality at far lower
  latency; use them when the cross-encoder is over budget.
- Log reranker scores per chunk: they find weak query clusters and set a "no good result"
  abstain threshold.

## Query transformation

| Technique | Use when | Cost |
|---|---|---|
| Follow-up condensation | Multi-turn chat: history + new turn → one standalone query | 1 small LLM call |
| Rewrite | Real queries are badly worded or conversational | 1 LLM call |
| Multi-query / decomposition | Compound or comparison questions | N retrievals |
| Multi-query + RRF | As above, fused | N retrievals + fusion |
| Step-back | Specific question needs broader background | 1 call + 1 retrieval |
| HyDE (embed a hypothetical answer) | No labels; query and document vocabulary differ | 1 LLM call |

Skip it when queries are keyword-like or contain exact IDs (rewrites drop them), when the
latency budget can't take an extra call (~0.5–2 s), when it hasn't raised recall on your
set, or when question-aligned chunks can do the work at ingestion.

## Filters and query understanding

- **Hard constraints are filters, never similarity.** Numeric limits ("under $200"),
  negations ("not black"), minimums ("4 stars and up"), dates and "latest" are rules; vector
  search treats them as hints, so a $350 item can outrank a $180 one. Pipeline: extract
  constraints → hard filter → hybrid search within survivors → rerank.

  | Question | Tool |
  |---|---|
  | "Which rows match?", counts, aggregates | Text-to-SQL or a filter API |
  | "What is this about?" | Vector / hybrid search |
  | "Most relevant items that satisfy X" | Filter, then vector / hybrid |

- **Extraction contract:** only fields present in the query (no defaults, no invented
  values), a closed field list per domain, one operator vocabulary any backend can translate.
  Validate the output; fall back to unfiltered search on a parse failure.

  ```json
  {"category": "eq:shoes", "price": "lt:200", "colour": "ne:black", "rating": "gte:4",
   "date": "between:2025-01-01:2025-06-30"}
  ```

- **The parser runs on every query; size it for the hot path.** Start with a prompted model
  and an eval (`rag-evaluation.md`: key F1, value accuracy, parse rate). The task is bounded,
  so a small (< 1B) fine-tuned model can reach ~0.9 key F1 and ~98% parse rate at a fraction
  of the cost and latency; fine-tune only when cost or latency demands it (`agent-accuracy`).
- **Access-control filters come from the authenticated user in code.** A filter the model
  can omit is not a permission check.
- **Cluster real queries by topic and by needed capability** (tables, comparisons,
  deadlines, images); route capabilities to specialised indexes or tools. A growing "Other"
  cluster means drift.

## Context assembly

- Pass the reranked top few, not everything retrieved.
- Put the most relevant chunks first and last; the middle is used worst.
- Deduplicate near-identical chunks; merge adjacent chunks from one document.
- Wrap each chunk with ID, title, date and heading path (`<document id="…">`) so the model
  can cite and prefer the newest.
- When chunks disagree (old vs new policy), keep the newer by metadata or tell the model how
  to choose.
- Long documents (20k+ tokens): documents first, question last.

## Citations and grounding

- Use the provider's native citations API where available (more reliable pointers than
  prompted citations); map one chunk per content block so citations resolve to chunk IDs.
  Verify against current provider docs (some can't combine with structured outputs).
- Without native support:
  - Allow "I don't know" and say what to do instead (escalate, ask a clarifying question).
  - Over 20k tokens: extract verbatim quotes first, answer only from them.
  - Post-verify each claim against a quote; retract unsupported ones.
- **Check in code that cited IDs ⊆ retrieved IDs.** Free, deterministic eval.

## Agentic RAG

- Expose retrieval as tools: `search(query, filters)`, `grep`, `fetch(doc_id)`, SQL. Return
  IDs, titles and short snippets so the agent chooses what to read. Tool design → `agent-tools`.
- Long research: run searches in sub-agents returning 1,000–2,000-token summaries with source
  IDs (`agent-context`).
- Evaluate every retrieval call with retrieval metrics from its span, plus trajectory checks:
  redundant searches, results never read, source quality (agents drift to SEO content farms;
  have a human review sources).
- **Table-of-contents navigation** for long structured documents: a section tree with a
  summary per node and tools to list children and read a node. Keeps natural boundaries and
  an auditable path; can far outperform vector RAG on filings and manuals — measure on yours.
- Expect 3–10 searches per request: the store's p99, not its mean, sets response time.
  Choose agentic RAG per corpus with an eval.

## Graph retrieval (last lever)

- Only when failures are about relationships across entities (multi-hop "which suppliers of
  X are exposed to Y") and hybrid + rerank + agentic search are measured and fall short.
- Shape: extract query entities → vector search for entry nodes → traverse for related facts
  → merge with vector candidates → rerank. The vector index must return node IDs in metadata.
- Corpus entity extraction is its own error-prone pipeline; label multi-hop queries first.
