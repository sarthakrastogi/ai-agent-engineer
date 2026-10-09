# Architecture Overview

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         EMPLOYEE                                │
│                    (Uses CLI or integration)                     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ Q: "How much leave do I get?"
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    HR_AGENT.PY (Main Agent)                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ interactive_mode()     or     answer_question()           │ │
│  │  - Multi-turn REPL          - Single LLM call             │ │
│  │  - Maintains history        - Caches policies             │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ A: "20 days + 5 carry-over"
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                ANTHROPIC CLAUDE API (claude-opus-5-5)            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ System Prompt (with cache_control: ephemeral)             │ │
│  │ ┌──────────────────────────────────────────────────────┐  │ │
│  │ │ - Instructions: cite sources, stay in policies      │  │ │
│  │ │ - All 5 policies concatenated (~3KB)                │  │ │
│  │ │ - Cached after first query (5 min TTL)              │  │ │
│  │ └──────────────────────────────────────────────────────┘  │ │
│  │ Conversation History (not cached)                         │ │
│  │ ┌──────────────────────────────────────────────────────┐  │ │
│  │ │ [User Q1, Assistant A1, User Q2, ...]                │  │ │
│  │ └──────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### First Query (with cache creation)

```
User Question
    │
    ▼
load_policies() ──────┐
    │                 │
    └─ policies/*.md  ▼
          │      format_policies_for_context()
          │            │
          │            ▼
          └───────► create_system_prompt()
                         │
                         ▼
                   answer_question()
                         │
                         ├─ conversation_history = [{"role": "user", "content": Q}]
                         │
                         ▼
                   client.messages.create(
                         model="claude-opus-5-5",
                         system=[{
                             type: "text",
                             text: POLICIES_AND_INSTRUCTIONS,
                             cache_control: {type: "ephemeral"}  ◄─ CACHE CREATE
                         }],
                         messages=conversation_history
                   )
                         │
                         ▼
                   Extract response text
                         │
                         ├─ Add to history
                         │
                         ▼
                   Answer to user
                   
Cost: Full prompt tokens (1000) @ full rate ≈ $0.0015
Time: 1-2 seconds (network + inference)
```

### Subsequent Queries (with cache hit)

```
User Follow-up Q
    │
    ▼
answer_question()
    │
    ├─ conversation_history = [Q1, A1, Q2, A2, ..., NEW_Q]
    │
    ▼
client.messages.create(
    system=[{
        type: "text",
        text: SAME_POLICIES_AND_INSTRUCTIONS,
        cache_control: {type: "ephemeral"}  ◄─ CACHE HIT
    }],
    messages=conversation_history
)
    │
    ▼
response includes:
    usage: {
        input_tokens: 100,
        cache_read_input_tokens: 1000  ◄─ REUSED
    }
    │
    ▼
Answer to user

Cost: 100 new tokens @ full rate + 1000 cached @ 10% rate = $0.00015
Time: <500ms (cache hit is fast)
```

## Component Interaction

```
┌────────────────┐
│  hr_agent.py   │ Main module
│                │
│ load_policies()│ ────► Read policies/*.md files
│   │            │
│   └────► dict  │ {name: content, name: content, ...}
│                │
│format_policies │ ────► String concatenation
│   │            │
│   └────► str   │ "# HR POLICIES\n## Policy: LEAVE\n..."
│                │
│create_system   │ ────► Embed in instructions
│_prompt()       │
│   │            │
│   └────► str   │ "You are an HR Assistant. Policies:\n..."
│                │
│answer_question │ ────► Single LLM API call
│   │            │       (with cache_control in system)
│   │            │
│   ├─ Q ────────┤ ──► messages=[{role: user, content: Q}]
│   │            │
│   └─ A ◄───────┤ ◄── response.content[0].text
│                │
│interactive_    │ ────► REPL loop
│mode()          │
│                │
│main()          │ ────► Entry point (CLI or single-Q)
└────────────────┘
```

## Cache Lifecycle

```
Session Start
│
├─ User asks Q1
│  └─ System prompt + policies loaded
│  └─ Cache created: 1000 tokens @ full rate
│  └─ TTL starts: 5 minutes
│
├─ User asks Q2 (within 5 min)
│  └─ Cache hit: policies reused
│  └─ TTL reset: 5 more minutes
│  └─ Cost: 90% savings on policies
│
├─ User asks Q3 (within 5 min)
│  └─ Cache hit again
│  └─ TTL reset
│  └─ Cost: 90% savings
│
└─ 5+ minutes of inactivity
   └─ Cache expires
   └─ Next query: creates new cache (same cost as Q1)
```

## Error Handling Flow

```
                    ┌─ Missing API key?
                    │  ▼
                    │  AuthenticationError
                    │
answer_question()   │
    │               ├─ Policy file not found?
    ▼               │  ▼
Call Anthropic API  │  FileNotFoundError (at startup)
    │               │
    ├─ Network error?
    │  ▼
    │  APIConnectionError → retry with backoff
    │
    ├─ Rate limit?
    │  ▼
    │  RateLimitError → retry with backoff
    │
    ├─ Question not in policies?
    │  ▼
    │  Agent responds: "Not covered by current policies"
    │
    └─ Success
       ▼
       Return answer + citation
```

## Memory/State

```
During Session:
┌────────────────────────────────────────┐
│ conversation_history (in memory)       │
├────────────────────────────────────────┤
│ [{role: user, content: "Q1"}           │
│ {role: assistant, content: "A1"}       │
│ {role: user, content: "Q2"}            │
│ {role: assistant, content: "A2"}]      │
└────────────────────────────────────────┘
       │
       ├─ Grows with each exchange
       ├─ Passed to LLM each time (for multi-turn context)
       ├─ Cleared when session ends
       └─ NOT persisted to disk

Policies (in memory):
┌────────────────────────────────────────┐
│ policies dict                          │
├────────────────────────────────────────┤
│ {                                      │
│  "leave": "# Leave policy...",         │
│  "expenses": "# Expenses policy...",   │
│  "remote-work": "# Remote work...",    │
│  "travel": "# Travel policy...",       │
│  "equipment": "# Equipment policy..."  │
│ }                                      │
└────────────────────────────────────────┘
       │
       ├─ Loaded once at startup
       ├─ Formatted into system prompt
       ├─ Cached by Anthropic (5 min)
       └─ NOT modified during session
```

## Scaling Considerations

### Current Setup (Single Machine, ~5 small policies)

- ✅ Works: 1-100 users sequentially
- ✅ Cost: ~$0.30/month for 100 q/day
- ✅ Latency: <500ms per question
- ⚠️ Concurrency: Single-threaded, queued

### If Usage Grows (>1K questions/day)

| Need | Solution | Effort |
|---|---|---|
| Concurrency | Multi-threaded wrapper or async | 1-2 hours |
| Rate limits | Queue + backoff (SDK handles) | Built-in |
| Cost tracking | Log tokens, aggregate | 1 hour |
| Load balancing | Multiple API keys, round-robin | 2 hours |
| High availability | Retry logic + fallbacks | 2-3 hours |

### If Policies Grow (>100 KB)

| Need | Solution | Effort |
|---|---|---|
| Retrieval | Hybrid search (BM25 + embeddings) | 8 hours |
| Storage | Vector DB (Pinecone, Weaviate) | 4 hours setup |
| Chunking | Semantic splits per policy section | 2 hours |
| Versioning | Policy version tracking | 3 hours |

## Security Model

```
Threat: Prompt injection in user question
├─ Mitigation: Only user content in messages[], not system
├─ System prompt fixed: policies + instructions immutable
└─ Risk: Low (user can't inject into cached system)

Threat: Policy data leakage
├─ Mitigation: HTTPS to Anthropic, ephemeral cache
├─ Storage: Plaintext files, not sensitive
└─ Risk: Low (policies are non-confidential)

Threat: API key exposure
├─ Mitigation: Environment variable, not in code
├─ Best practice: Rotate key if leaked
└─ Risk: Low (dev environment only)

Threat: Unauthorized access to agent
├─ Mitigation: None in current design (local CLI only)
├─ If deployed: Add auth layer (Flask, OAuth, Slack tokens)
└─ Risk: Medium for web/Slack (add auth first)
```

## Testing Architecture

```
test_agent.py
├─ Loads policies from disk
├─ Runs 7 test questions through agent
│  ├─ Q1: "How much annual leave?"
│  ├─ Q2: "Carry-over rules?"
│  ├─ Q3: "Expense limits?"
│  ├─ Q4: "Remote work days?"
│  ├─ Q5: "Travel class?"
│  ├─ Q6: "Equipment refresh?"
│  └─ Q7: "Pet insurance?" (not in policies)
├─ Maintains conversation_history across Qs
│  └─ Verifies multi-turn context preserved
├─ Output: Q&A pairs for manual review
└─ No automated grading (would need eval framework)

Manual verification:
├─ Does each A cite the policy?
├─ Is Q7 properly escalated to HR?
└─ Does multi-turn context work?
```

---

**Version:** 1.0  
**Last updated:** 2024-10-09
