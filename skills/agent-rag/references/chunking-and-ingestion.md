# Chunking and ingestion

## Parsing

Ingestion failures are invisible until someone reads the parsed text. **Read the parsed
output of ~20 representative documents before tuning anything downstream.** Look for merged
columns, repeated headers/footers, page numbers mid-sentence, scanned pages with no text
(needs OCR), lost list structure, tables flattened into runs of numbers.

- **Structured documents need a layout-aware parser** that labels titles, headings,
  paragraphs, tables, lists and figures. Judge it by its output, not its feature list.
- **Tables:**
  - Keep each table whole with its caption and header row. If it must split, split by row
    and repeat the header in every piece.
  - Serialise so each cell sits next to its column name (Markdown table or `column: value`).
  - Keep the explanatory paragraph before the table as its title; a table without its "why"
    invites a hallucinated one.
  - Unmerge merged cells, copying the value into each cell.
  - Large or dense tables: index an LLM-written description, store the full table, return
    the full table on a hit.
- **Lists:** repeat the list header in every chunk holding list items.
- **Images and diagrams:** store a vision-model description as a text chunk linked to the
  image; pass the image to a multimodal model on a hit. Captions only is the cheap fallback.
- **Headings:** keep the hierarchy (HTML/Markdown headings, PDF outline, DOCX styles).
- **Boilerplate:** strip navigation, banners, legal footers, templates; they create
  near-duplicates that crowd out real results.
- **Metadata per document:** stable `doc_id`, source path/URL, title, owner, created and
  updated dates, type, version, access-control groups.
- **Metadata per chunk:** heading path, `parent_chunk_id`, source page, parser confidence
  if structure detection is ML-based. Add entities or status only when a filter or ranking
  rule uses them.
- **Make ingestion idempotent and re-runnable.** Record parser, chunker settings and
  embedding model + version in the index metadata so a trace can say which index answered.
- Label relevance by document span, not chunk ID (`rag-evaluation.md`).

## Chunk size and overlap

- **Grid-search size and overlap against recall@k** on the labelled set. Expected spread:
  chunking alone moves recall by up to ~9 points. A recursive splitter at 200 tokens, no
  overlap, is a strong baseline; LLM-based chunkers edge it; 800 tokens / 400 overlap
  scores worst.
- **Starting grid:** recursive, structure-aware splitter at 200, 400, 800 tokens × overlap 0
  and ~10–15%. Add a semantic or LLM chunker only if a measured gap remains. For large
  multi-page PDFs/reports, add page-level chunks as a candidate.
- **Structure beats the token target.** Never cut a section, clause, procedure, table row or
  code function to hit a size; a complete 400-token section beats a broken 250-token one.
- **Match size to the task:** fixed-answer extraction → the largest chunk that still holds
  the whole answer; summaries and exhaustive extraction → small chunks, map-reduce.
- Read the chunks before touching the embedder; bad boundaries waste embedder tuning.

```text
for size in [200, 400, 800]:
  for overlap in [0, 0.1 * size]:
    index = build_index(corpus, splitter=recursive(size, overlap, respect=headings))
    report(size, overlap, recall_at_k(index, labelled_set, k=K_CANDIDATE), index_tokens)
pick the smallest config within noise of the best recall; log it in experiment-log.md
```

### Route by document type

Classify documents, route each type to its own pipeline, keep one metadata schema.

| Type | Start with | Watch for |
|---|---|---|
| Financial reports, data sheets | Layout-aware + table handling | Numbers detached from explanation; merged cells |
| Contracts, regulations | Clause boundaries from numbering/indentation; never split a clause; 10–20% overlap | Liability clause retrieved without its "except" / "provided that" |
| Technical manuals | Heading path; keep each procedure and code block whole, or steps as children | Diagrams separated from text; cross-references ("see 4.2") → store in metadata |
| Clinical / case notes | Link a record's sections by metadata; keep dates with each fact | Medication split from its interaction warning |
| Unstructured prose, chat logs | Recursive grid; semantic chunker as a candidate | Topic shifts mid-chunk |

## Contextual chunk headers (do first)

Prepend the document title and heading path to every chunk
(`Employee Handbook > Leave > Parental leave`), plus path, author, date and tags. Put them
in the chunk text, not only in metadata fields, so both BM25 and dense retrieval see them.

## Contextual retrieval

When headers leave a recall gap: a small model reads the whole document plus the chunk and
writes 50–100 tokens situating the chunk; prepend that **before both embedding and BM25
indexing**.

- Expected effect on retrieval failures (1 − recall@20): contextual embeddings −35%,
  + contextual BM25 −49%, + reranking −67%.
- Cost: about $1 per million document tokens with prompt caching on the document; one-off
  per document version.
- Prompt shape: "Give a short succinct context to situate this chunk within the overall
  document for the purposes of improving search retrieval." Adapt to the domain and version
  it like any prompt.

**Late chunking** is the alternative when the embedder exposes token-level outputs: embed
the whole document with a long-context (≥ 8k) embedder, then mean-pool token vectors per
chunk. Gains grow with document length.

## Parent–child chunks

When small chunks retrieve precisely but answers need surrounding context: 1,000–2,000-token
parents, 200–500-token children, index only children, pass each hit's parent to the model,
dedupe parents. Measure recall on children, answer quality on parents.

## Multi-representation indexing

Index several representations that all point to the same chunk: raw text, a summary, key
terms, and the questions it answers. Question-aligned indexing (generate likely questions
per chunk) moves HyDE/rewrite cost from query time to ingestion. Return the chunk, not the
representation.

## Proposition chunking

An LLM rewrites sentences into standalone propositions ("He led Apollo 11" → "Neil Armstrong
led NASA's Apollo 11 mission") and groups them. Several LLM calls per document: use only on
high-value corpora (legal, medical, support KBs) when the grid and contextual retrieval
leave a measured gap.
