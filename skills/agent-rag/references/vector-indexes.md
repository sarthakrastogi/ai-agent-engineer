# Vector indexes

## ANN loses recall — measure it

- Vector stores return approximate neighbours: one more recall loss, below the embedder.
- **On a sample of labelled queries, compare the index's top-k with exact search** over the
  same vectors. If exact finds the gold chunk and the index doesn't, tune the index before
  touching the embedder or chunking. Re-check after changing index parameters.
- For RAG, what counts is **recall at the candidate k**: a reranker can't recover a chunk the
  index never returned. Keep `ef_search` ≥ candidate k.
- Small corpora don't need ANN: exact search or a vector column in your existing database.

## Index types

| Index | Use when | Cost |
|---|---|---|
| **HNSW** (default) | Most workloads | Raw vectors in RAM; slow to build |
| **IVF** | Data clusters well, or frequent rebuilds (cheaper to build) | Recall depends on clustering and clusters probed |
| **PQ** | Memory is the bottleneck | 10–100× compression, lossy recall |
| **LSH** | Binary or low-dimensional vectors | Specialised |

## Tuning

- Pick the recall you need on the labelled set, then the cheapest setting that reaches it;
  95% recall can be ~10× faster than 99% and often good enough.
- **HNSW:** `M` (links per node: recall vs memory and build time), `ef_construction` (build
  quality), `ef_search` (per-query recall vs latency). Sweep `ef_search` and plot recall@k
  against p95 latency; never keep defaults unmeasured.
- Frequent re-indexing (chunking experiments, re-embeds) can make HNSW build time dominate;
  consider IVF.

## Filtered search

- Filters (tenant, ACL, date, type) can make queries 10–100× slower: the graph spans the
  whole collection, so the search visits many nodes to find a few that pass.
- Options: native metadata indexing or pre-filtering; separate indexes or partitions per
  high-cardinality value (per tenant); for very selective filters, filter in a database and
  search the survivors exactly.
- Benchmark filtered queries at realistic selectivity before choosing a store. ACL filters
  are mandatory, so their latency is part of the budget.

## Operations

- **Not OLTP.** Deletes are tombstones, updates are delete + insert; churn degrades graph
  connectivity. Batch updates, re-index periodically, track recall after heavy churn.
- **Sharding:** fan-out to all shards means the slowest sets p99; routed shards are faster
  but can miss neighbours.
- **Cold start:** warm HNSW into memory after deploys and restarts.

## Match the store to the pattern

| Pattern | Optimise for |
|---|---|
| Single retrieval per request | Per-query latency |
| Hybrid BM25 + dense | Native hybrid, or two queries fused in code |
| Retrieve → rerank (over-fetch ~100) | Recall at candidate k, verified against exact search |
| Agentic, 3–10 bursty queries | Consistent p99 |
| Graph retrieval | Node IDs in metadata; filter performance |

## Memory and cost

- Raw vectors dominate: a 1,536-d float32 vector is ~6 KB; HNSW links add ~M·2·4 B per
  vector (~128 B at M=16). Use PQ or fewer dimensions only after measuring the recall cost.
- Don't over-provision for recall you haven't shown you need; at scale self-hosting may beat
  managed pricing.
