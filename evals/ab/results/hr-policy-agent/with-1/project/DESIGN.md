# HR Policy Agent - Design Document

## Overview

The HR Policy Agent is a lightweight Python application that answers employee questions about company HR policies using Claude LLM. It was designed to be simple, reliable, and maintainable.

## Architecture Decision

**Single LLM call with context embedding** (not an agent loop)

### Why this shape?

We rejected more complex architectures because:

1. **Fixed, small knowledge base** — All HR policies total ~2KB and don't change mid-conversation
2. **Single-answer questions** — Each question has one correct answer based on policy
3. **No judgment loops** — No need for multi-turn reasoning, self-correction, or tool failures
4. **Deterministic accuracy** — With all policies in context, the LLM gives consistent, citable answers

### Why NOT an agent?

An agentic loop would add unnecessary complexity:
- Higher latency (multiple API calls instead of one)
- Higher cost (~4x tokens for tool use overhead)
- No benefit — policies don't change; failures are rare
- Harder to debug and trace

### Why NOT semantic retrieval?

If we had 100+ policies or real-time updates, we'd add:
- Vector embeddings for relevance search
- Chunking and retrieval ranking
- Just-in-time context loading

With current scope (~2KB), full context is simpler and faster.

## System Design

```
User Question
    ↓
load_policies() ← read all markdown files
    ↓
build_system_prompt() ← embed policies + instructions
    ↓
complete() ← single Claude API call
    ↓
text_of() ← extract response text
    ↓
Cited Answer
```

## Components

### `agent.py` — Main module

**`load_policies(policies_dir)`**
- Reads all `.md` files from `policies/` directory
- Returns concatenated markdown as a single string
- O(n) where n = number of policy files (currently 5)

**`build_system_prompt(policies_text)`**
- Wraps policies in system prompt with instructions
- Enforces:
  - Answer from policies only (no synthesis)
  - Always cite relevant section
  - Acknowledge gaps when applicable
  - Professional, conversational tone

**`answer_question(question, policies_dir)`**
- Orchestrator function
- Loads policies once per call (could cache if handling many questions)
- Calls `complete()` with built prompt
- Returns final answer as string

### `llm.py` — API wrapper

Pre-existing wrapper over Anthropic Messages API:
- Lazy imports `anthropic` (tests can mock it)
- Supports optional tools (for future extensibility)
- Returns raw response object; caller extracts text

### `test_agent.py` — Test suite

Three test classes:

1. **`TestPoliciesLoading`** — Unit tests
   - Verify files load successfully
   - Check all policy sections present

2. **`TestSystemPrompt`** — Unit tests
   - Verify prompt structure and instructions

3. **`TestAgentResponses`** — Integration tests (requires API key)
   - Five policy questions with ground-truth keywords
   - One out-of-scope question (salary) to test gap handling
   - Verify answers contain policy terms, not hallucinations

## Key Decisions

### 1. Embed all policies in system prompt

**Pros:**
- Simple, single API call
- Policies are small (2KB)
- Fully deterministic (same policies every time)
- Easy to update (just edit markdown)

**Cons:**
- Won't scale to 100+ large policies
- No semantic ranking (all policies equally visible)

**Decision:** Start simple; add retrieval if policies grow.

### 2. No tool use

**Why not tools?**
- Writing tools (file a request, approve a request) need approval guardrails
- Reading tools (check balance, get history) need auth/permissions
- Query time cost is high for benefit

**Future:** `agent-tools` + `agent-guardrails` if we add write operations.

### 3. No memory or multi-turn

**Why not?**
- Each question is independent
- Follow-ups work with new question + full context
- No ambiguity or session state needed

**Future:** Add message history if multi-turn context matters.

### 4. Single model (Claude Sonnet 5.5)

**Why Sonnet?**
- Fast enough for single-call use
- Accurate for policy Q&A
- Cost-effective
- Model can be overridden via `MODEL` env var for testing

**Future:** Benchmark against Haiku if volume grows; keep Sonnet for accuracy.

## Testing Strategy

### Unit tests (no API)
- `TestPoliciesLoading` — file I/O
- `TestSystemPrompt` — prompt assembly

Run with: `pytest test_agent.py::TestPoliciesLoading -v`

### Integration tests (requires API key)
- `TestAgentResponses` — full end-to-end flow
- Five real questions with policy answers
- One out-of-scope question to verify gap handling

Run with: `ANTHROPIC_API_KEY=... pytest test_agent.py::TestAgentResponses -v`

### Manual testing
- `example.py` — runs 5 sample questions interactively
- `python agent.py "question"` — CLI mode

## Failure modes and mitigations

| Failure | Cause | Mitigation |
|---------|-------|-----------|
| Hallucinated policy | System prompt unclear | System prompt forbids synthesis; cite constraint; model reliability |
| Out-of-scope answer | Policies too broad | Example in prompt: "salary not covered" |
| Latency | Network issues | Single call means <1 second typical |
| Stale answers | Policy updates | Update `.md` files; re-deploy; no caching |
| API errors | Rate limits, quota | Bare SDK (no retry logic yet); add if needed |

## Future enhancements

1. **Caching** — Load policies once at startup, not per question
2. **Conversation history** — Keep message history for follow-ups
3. **Tool use** — Add tools when policies need write operations (file request, etc.)
4. **Semantic retrieval** — Add vector search if policies >50KB
5. **Observability** — Log questions, answers, costs to trace quality
6. **Approvals** — Add human-in-loop for sensitive operations

## Deployment

### Local

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
python agent.py "your question"
```

### As a library

```python
from agent import answer_question
answer = answer_question("How much leave do I get?")
```

### As a service

Wrap `answer_question()` in a Flask/FastAPI endpoint:

```python
@app.post("/ask")
def ask(question: str):
    return {"answer": answer_question(question)}
```

## Success metrics

1. **Accuracy** — Answers match official policy wording (target: 100% on test set)
2. **No hallucinations** — All claims are from policies, not invented (target: 0%)
3. **Latency** — <1s per question (target: <500ms typical)
4. **Cost** — ~0.3¢ per question at current volume (target: <1¢)

## References

- Architecture: Single-call LLM vs. agent loop decision (agent-design)
- If adding tools: agent-tools skill
- If adding retrieval: agent-rag skill
- If adding evals: agent-evals skill
