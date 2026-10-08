# RAG evaluation

## Separate retrieval from generation

- Score retrieval with IR metrics against labels; score generation with error analysis and
  validated judges (`agent-evals`). A good answer on bad retrieval is luck.
- Never grade answers with ROUGE, BERTScore or cosine similarity.

## Retrieval metrics

| Metric | Use for |
|---|---|
| **Recall@k** | First-stage retrieval, the primary metric: the model can ignore irrelevant content but can't generate from missing content |
| Precision@k | The reranked / final-k stage |
| MRR | Single-fact lookups with one right chunk |
| nDCG@k | Graded relevance; pair with recall |

- **Measure at two k:** candidate k before reranking (does it enter the shortlist?) and final
  k (does it survive the cut?).
- Report per query cluster, not only overall; a 90% average hides a 40% cluster.
- Retrieval evals make no LLM calls: run them on every chunking, embedding, filter or
  ranking change.
- ANN recall is its own layer: compare with exact search (`retrieval-and-ranking.md` →
  Vector index).

### Constraint satisfaction (filtered search)

Relevance metrics miss a relevant item that breaks a rule.

| Metric | Definition |
|---|---|
| Per-constraint satisfaction@k | Fraction of top-k satisfying one constraint type |
| Overall@k | Fraction of top-k satisfying every constraint in its query |
| Perfect@k | 1 if every top-k result satisfies every constraint, else 0; mean over queries |

- Filter-then-search should score ~1.0. Lower means constraints are leaking into similarity;
  similarity-only ranking typically fails exclusions and attributes like colour.
- **Score the query parser separately:** key F1 (right fields), value accuracy (right values
  and operators), parse rate (valid output). A parser bug looks like a retrieval bug.

## Building the labelled set

Start with **20–50 query → relevant-span pairs** and grow from production; 50–100 for a
strategy comparison. Mix difficulty, roughly 30% single-fact, 50% multi-chunk ("why did Q3
revenue fall?"), 20% synthesis; an easy-only set hides chunking failures.

1. **Real queries first** from logs, tickets or interviews; a domain expert marks where the
   answer lives.
2. **Synthetic per chunk** for coverage: extract one fact, write a question a user would ask
   without copying the chunk's wording.
3. **Adversarial:** questions reusing vocabulary from a similar chunk that doesn't answer
   them, to catch keyword-overlap false positives.
4. **Filter for realism:** rate synthetic queries 1–5 for "a real user would ask this", keep
   ≥ 4. Keep validating on real queries.
5. **Label spans, not chunk IDs:** `doc_id` + character range. A chunk is relevant if it
   overlaps the span, so labels survive re-chunking.
6. **Record provenance** (real / synthetic / adversarial, date, labeller) in the file header
   or `datasets/README`; hold out a test split you don't tune on.

```jsonl
{"id":"q017","query":"How long is parental leave after 6 months' service?","relevant":[{"doc_id":"handbook-v7","span":[18200,18950]}],"source":"real","cluster":"policy-lookup"}
{"id":"q018","query":"Is there a probation period for parental leave?","relevant":[],"source":"adversarial","cluster":"policy-lookup"}
```

Empty `relevant` marks an unanswerable query: it tests abstention, not recall.

```python
def overlaps(r, g):
    return r.doc_id == g["doc_id"] and r.start < g["span"][1] and r.end > g["span"][0]

def recall_at_k(results, item, k):          # results: ranked chunks with doc_id, start, end
    gold = item["relevant"]
    if not gold: return None                 # unanswerable: skip in the recall mean
    covered = [g for g in gold if any(overlaps(r, g) for r in results[:k])]
    return len(covered) / len(gold)          # fraction of gold spans retrieved

def hit_at_k(results, item, k):              # 1 if any gold span is in the top-k
    r = recall_at_k(results, item, k)
    return None if r is None else float(r > 0)
```

Use recall@k for multi-chunk questions; hit@k hides partially retrieved answers.

## Generation metrics

| Metric | Question | Needs |
|---|---|---|
| Faithfulness | Supported claims ÷ total claims, against retrieved context | — |
| Answer relevance | Does it answer the question asked? | — |
| Completeness | Is every sub-question of a multi-part question answered? | Sub-questions |
| Context relevance | Is the passed context about the question? | — |
| Context recall / correctness | Did context and answer cover the reference? | Reference answer |
| Citation validity | Cited IDs ⊆ retrieved IDs (code); each cited chunk supports its claim | — |
| Abstention | Says it doesn't know on unanswerable queries | Unanswerable set |

- **RAGAS-style scores are unvalidated LLM judges.** Validate like any judge (`agent-evals`):
  ~100 balanced human labels, TPR and TNR > 0.9. Prefer binary pass/fail per claim or answer.
- **Faithfulness ≠ completeness.** Answering half of a two-part question scores perfect
  faithfulness; decompose and check each part.
- A small hallucination classifier (e.g. HHEM) is a cheaper faithfulness option than an LLM
  judge.
- **Starting targets for critical use:** context relevance > 80%, faithfulness > 90%,
  completeness > 85%. Agree real thresholds with the user.
- **Cadence:** retrieval metrics on every change; context relevance, faithfulness, answer
  relevance per release; coverage and answerability monthly.
- **Report quality with cost:** every change logs recall delta, added p95 latency and cost
  per query (`experiment-log.md` if used).
- **A/B variants on the same queries;** have a human review the queries where they disagree.

## Where it lives (if the project uses `agent-engineering/`)

- Retrieval and generation rows in `eval-plan.md` (grader, threshold, dataset).
- Labelled set in `datasets/retrieval-<name>.jsonl`.
- Online: score sampled production traces from retrieval spans (`agent-observability` must
  log chunk IDs, scores and content).
