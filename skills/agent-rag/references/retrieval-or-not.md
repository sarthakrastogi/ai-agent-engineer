# Retrieval or not

Decide before anyone picks a vector DB.

## 1. Is it a knowledge problem?

Classify 5–10 failing examples. If most are behaviour failures, stop: RAG on a behaviour
problem can lower accuracy.

| Symptom | Problem | Fix |
|---|---|---|
| Lacks a fact that exists in your data | Knowledge | Retrieval |
| Uses an outdated version of a fact | Freshness | Retrieval with re-indexing and date metadata |
| Classifier applies an out-of-date policy or taxonomy | Freshness | Retrieve the current policy text at decision time instead of retraining |
| Wrong format, tone, style, inconsistent | Behaviour | `agent-prompting`, `agent-accuracy` |
| Wrong tool or bad arguments | Tool design | `agent-tools` |
| Forgets earlier turns or decisions | Context over a run | `agent-context` |

- **Both?** Behaviour goes in the prompt or a fine-tune; facts (prices, account data,
  current policy) go through retrieval. Confirm both are needed: the combination is harder
  to debug.
- Fine-tuning doesn't fix missing knowledge; it can make domain hallucinations more confident.

## 2. Ask the user

- Corpus size (tokens or pages) and change rate.
- Query types: single-fact, comparison, "latest X", summary, multi-hop, code navigation.
  Get 20 real ones if they exist.
- Latency and cost budget per query.
- Per-user permissions? Then the search layer enforces them (`agent-guardrails`).
- Structured (SQL, APIs, code, file trees) or unstructured (PDFs, wiki, tickets)?

## 3. Pick the shape

| Corpus and queries | Shape |
|---|---|
| Static, < ~200k tokens (~500 pages), below your measured quality ceiling | Whole corpus in the prompt with caching |
| Large or changing, fact lookup, tight latency/cost | Hybrid BM25 + dense with reranking |
| Code, file trees, APIs, SQL | Agentic search tools: grep, glob, SQL, fetch |
| Multi-hop or exploratory | Search as a tool the agent calls repeatedly |
| Few long structured documents (filings, manuals, contracts) | Table-of-contents navigation (`retrieval-and-ranking.md`) |
| Hard constraints over items with fields | Extract filters, then search within them |
| Mixed query types | Route per type to different indexes or tools |
| Complexity varies widely | Route: no retrieval / one retrieval / iterative search |

- **Whole-corpus prompts still degrade.** Accuracy falls with input length and distractors,
  and the middle is used worst; a focused prompt can beat the full corpus well under 200k.
  Measure on your eval set before trusting it.
- **Long context tends to beat RAG on accuracy, RAG is far cheaper.** Letting the model
  decide per query whether retrieved chunks suffice or it needs the full context keeps most
  of the accuracy at much lower cost.
- **Default for agents:** load the small, always-needed context up front, fetch the rest just
  in time with tools. Cache what rarely changes and is used on every request; retrieve what
  must stay fresh.
- **Routers fail silently.** Evaluate router accuracy on labelled queries; a misroute to "no
  retrieval" is a recall failure nobody sees.
- Code and file trees favour grep and navigation; prose corpora still favour an index.
- Agentic vs classic RAG has no general answer: compare both on your labelled set.

## 4. Record it

Write the choice and rejected alternatives in `design.md` under "Knowledge sources /
retrieval" with corpus size, update cadence, query types and budget. Revisit when the corpus
outgrows the prompt or the query mix changes.
