# HR Policy Agent - Design Document

## Overview

A Python agent that answers employee questions about HR policies using Claude and prompt caching. Employees ask questions naturally, and the agent returns cited answers grounded in the company's HR policy documents.

## Architecture

### Design Choice: Single Call + Prompt Caching

**Why not a more complex pattern?**

| Alternative | Why rejected |
|---|---|
| **Workflow/multi-step** | Policies are static reference material; no intermediate decisions needed |
| **Agentic loop** | Policies fit in one context window; no search/iteration required |
| **Vector DB + RAG** | Only ~5 small policy files (~3KB total); retrieval overhead > benefit |
| **Multi-agent** | Single, well-scoped task; no parallel work |

**Why this pattern?**

1. **Simple**: One API call per question; conversation history handles multi-turn
2. **Cheap**: Prompt caching (0.9¢/K tokens cached) vs vector DB lookups
3. **Fast**: No retrieval latency; cache hits deliver answers in <500ms
4. **Accurate**: Claude sees all policies at once; no ranking/filtering can lose context
5. **Maintainable**: Add policies by dropping files in `policies/`; no re-indexing

### Context & Caching

```
System prompt (cached)
├── Instructions (be helpful, cite sources, don't make up policy)
└── Full policy content (~3KB)
    ├── policies/leave.md
    ├── policies/expenses.md
    ├── policies/remote-work.md
    ├── policies/travel.md
    └── policies/equipment.md

Conversation history (not cached)
├── User question 1
├── Assistant answer 1
├── User follow-up
└── Assistant follow-up
```

**Prompt cache hits on:**
- All subsequent questions in the same session (after first)
- New sessions with the same policies (if identical policy content)

**Estimated savings:**
- First query: 1000 input tokens @ full cost = ~$0.0015
- Cached queries: 1000 tokens @ 10% cost = ~$0.00015 each
- 100 queries: ~$0.0015 + (99 × $0.00015) ≈ $0.020

### Tool Design

This agent has **no tools** by design:

- ✅ Reading policies: Already in context
- ✅ Answering questions: LLM inference on context
- ✅ Formatting answers: LLM text generation
- ❌ No external APIs: HR system access requires auth and latency
- ❌ No side effects: No approvals, no submissions, no state changes

A tool would only help if we needed to:
- Retrieve changing/external data (we don't—policies are static)
- Take actions (we don't—we only answer)
- Reduce context size (we have plenty—3KB is tiny)

### Model Selection

**Claude Opus 5.5** (`claude-opus-5-5`)

- Most capable for instruction-following and citation accuracy
- Handles few-shot prompting if needed later
- Prompt caching available
- Cost-competitive for low-volume use

**Why not a smaller model?**
- Sonnet would work but is less reliable at sticking to policy text
- For ~$0.30/month, the extra quality is worth it
- Users expect HR answers to be reliable and unambiguous

## Conversation Flow

```
Employee                              Agent                         Anthropic API
    │                                  │                                  │
    ├─ asks question ───────────────► │                                  │
    │                                  │ ─── POST (with cache) ────────► │
    │                                  │  [1000 input tokens, new]        │
    │                                  │                                  │
    │                                  │ ◄── answer, cache token ─────── │
    │                                  │  [cache_creation_input=1000]     │
    │                                  │                                  │
    │◄─ answer with citation ────────── │                                │
    │                                  │                                  │
    ├─ follow-up question ──────────► │                                  │
    │                                  │ ─── POST (with cache) ────────► │
    │                                  │  [100 input tokens, cached]      │
    │                                  │                                  │
    │                                  │ ◄── answer, cache stats ─────── │
    │                                  │  [cache_read_input=1000]         │
    │                                  │                                  │
    │◄─ follow-up answer ─────────────  │                                │
```

## Code Structure

```
hr_agent.py
├── load_policies()              # Scan policies/ and read *.md files
├── format_policies_for_context()# Concatenate into one big string
├── create_system_prompt()       # Embed policies in system prompt
├── answer_question()            # Single LLM call with caching
│   └── client.messages.create() # Anthropic API with cache_control
└── interactive_mode()           # REPL for multi-turn
    └── main()                   # CLI entry point

test_agent.py
└── test_hr_agent()              # Run typical questions through agent
```

## Error Handling

| Scenario | Handling |
|---|---|
| Policy file not found | Raises `FileNotFoundError` at startup |
| API key missing | Anthropic SDK raises `AuthenticationError` |
| Question not in policies | Agent responds "not covered by current policies" |
| Malformed policy markdown | Shown as-is to Claude (Claude is forgiving) |
| API rate limit | SDK retries with backoff |
| Network error | SDK raises `APIConnectionError` (caller handles) |

## Observability

### What we log:
- Cache creation tokens (first call per session)
- Cache read tokens (subsequent calls)
- Token usage (input, output, cache)

### What we don't log (no privacy concerns):
- Policy content (already in plaintext files)
- Questions and answers (internal HR queries)
- Conversation history (session-scoped, not persisted)

## Security & Privacy

**Data at rest:**
- Policy files are plaintext markdown in `policies/`
- No sensitive data should go in policies (passwords, SSNs, etc.)
- Policies are read-only once in context; not logged by Anthropic

**Data in transit:**
- All API calls to Anthropic use HTTPS
- API key stored in environment variable (`ANTHROPIC_API_KEY`)
- Prompt caching token is ephemeral (5 min TTL)

**Access control:**
- No authentication in this agent (any user with API key can run)
- For Slack/web deployment, add your own auth layer

## Limitations

1. **Policies must be accurate** — Agent only repeats what's in policies
2. **No policy interpretation** — Won't say "this probably means..." or handle edge cases
3. **No external lookup** — Can't check payroll, approval systems, or employee data
4. **Conversation not persisted** — Each session is independent
5. **No real-time updates** — Changes to policies require restart

## Future Extensions

### Low effort, high value:
- **Slack integration**: Post policy questions in Slack, get answered
- **Citation links**: Hyperlink to policy file in answers
- **Policy version tracking**: "Updated 1 April 2026" in responses
- **Suggested questions**: "Did you mean...?" for clarification

### Medium effort:
- **HR system integration**: Look up employee details to personalize answers
- **Approval workflows**: Submit expense/leave requests via agent
- **Multiple languages**: Translate policies on-demand
- **Feedback loop**: Rate answers to detect when policies are unclear

### Deferred (wait for signal):
- **Vector DB**: Only if policies grow to 10+ MB or change frequently
- **Agent loop**: Only if we need multi-step reasoning
- **Multi-agent**: Only if HR data is split across domains

## Testing Strategy

**What we test:**
- Agent can load all policies ✓
- Agent cites sources ✓
- Agent handles questions outside policies ✓
- Agent maintains conversation context ✓
- Agent respects `cache_control` settings ✓

**What we don't test** (no eval framework):
- Factual accuracy (read-only, policies are the source)
- Tone/tone quality (subjective, read policy)
- Latency (depends on Anthropic API)
- Cost (depends on usage patterns)

**To add evals later:**
- Define "correct answer" as "matches [policy name], section [name]"
- Score 20-30 real employee questions against human labels
- Run monthly to catch policy drift

## Cost Estimate

**Per-query costs (estimated):**
- First query per session: ~$0.0015 (policies in context)
- Cached query: ~$0.00015 (10% of full cost)
- Average (50/50 new/cached): ~$0.00075/query

**Monthly estimate:**
- 100 queries/day (small team): ~$2.25/month
- 1000 queries/day (large org): ~$22.50/month
- 10K queries/day (very large): ~$225/month

(Based on Claude 3.5 Sonnet pricing; see Anthropic pricing docs)

## Decision Log

| Date | Decision | Why |
|---|---|---|
| 2024-10 | Single LLM call | Policies fit in context, no loops needed |
| 2024-10 | Prompt caching | Cost/latency tradeoff for multi-turn |
| 2024-10 | No tools | Policies static, no actions needed |
| 2024-10 | Opus 5.5 | Best accuracy/reliability for HR answers |
| 2024-10 | No vector DB | Too much overhead for small policy set |
