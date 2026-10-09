# HR Policy Agent Design

## Problem Statement

Employees need quick, accurate answers to HR policy questions. Manual HR support doesn't scale. The goal is to build a small, reliable agent that can answer common HR questions with citations to the actual policy documents.

## Success Criteria

- **Accuracy:** Answers match the policy text (100% citations for factual claims)
- **Latency:** <2 seconds per question (single LLM call, small context)
- **Cost:** <$0.01 per question (Claude Sonnet 5.5, ~200 tokens average)
- **Scope:** Refuses non-HR-policy questions with a helpful redirect to HR
- **Coverage:** Handles 90% of common employee questions about leave, remote work, expenses, equipment, travel

## Architecture

```
Employee Question
      ↓
  Retrieve (keyword matching)
      ↓
 Build system prompt with context
      ↓
 Call Claude (single turn, no tools)
      ↓
   Answer with citations
```

### Why this design?

1. **Single LLM call:** This is a retrieval + generation task. No loop needed. Employees ask one question, get one answer.

2. **Simple retrieval (keyword matching) instead of embeddings:**
   - Policy corpus is ~2k tokens (fits in prompt)
   - Policies are short, well-structured markdown with clear headers
   - Keywords are reliable (employees ask about "leave", "remote", "laptop", etc.)
   - Keyword matching is instant and deterministic
   - **Rejected:** Full-corpus context (works but no retrieval signal); embedding-based retrieval (over-engineered for this corpus size)

3. **No tools:** Questions don't require:
   - Database lookups (all info is in policies)
   - Approvals or side effects
   - Multi-step reasoning

4. **Retrieved context in system prompt:**
   - Keeps Claude's reasoning focused
   - Makes it easy to add new policies without changing the agent code
   - Ensures consistency (the prompt is the source of truth)

5. **Citation requirement in system prompt:**
   - Every answer must cite which policy it came from
   - Reduces hallucination (Claude won't invent policy details)
   - Employees can verify answers by reading the source

## Retrieval Strategy

**Keyword scoring:** Count word overlaps between the question and policy text, with a 2x boost for words appearing in headers.

**Top-k = 3:** Typical HR questions are specific enough that 2–3 policies contain the answer. Keeps context concise.

Example:
- Question: "How many days of leave do I get?"
- Words: {how, many, days, leave, do, i, get}
- Matches in leave.md (header + body): score 45
- Matches in expenses.md: score 3
- Matches in equipment.md: score 1
- Ranked: [leave.md, expenses.md, equipment.md] → return [leave.md]

## Trade-offs

| Choice | Benefit | Cost |
|--------|---------|------|
| Keyword matching | Simple, fast, no model | Misses synonyms ("vacation" vs "leave") |
| Top-k=3 | Concise, no context overflow | Might miss edge cases in 4th policy |
| No tools | Minimal complexity | Can't integrate with leave-booking system |
| Single call | Low latency, low cost | Can't ask clarifying follow-up questions |

## Known limitations

1. **Synonyms:** Keyword matching doesn't catch "vacation" → "leave" or "WFH" → "remote work". *Mitigation:* System prompt asks Claude to suggest related policies if no match.

2. **Numerical constraints:** Questions like "under $100" aren't parsed. *Mitigation:* Retrieval might miss an expense policy, but the LLM can ask the employee to be more specific.

3. **Multi-hop questions:** "Can I take parental leave while working remotely?" requires cross-policy reasoning. *Mitigation:* Claude does this reasoning; retrieval provides both policies.

4. **No follow-ups:** Each question is independent. *Mitigation:* Acceptable for an MVP; add multi-turn state if needed later.

## Measurement Plan

**Retrieval:** For a labelled test set of 20+ questions:
- Recall@3: Is the right policy in the top 3 results?
- Precision@3: Are all 3 results relevant?

**Generation (manual spot-check, not automated):**
- Citations present and correct
- Answer matches policy text (no hallucinations)
- Out-of-scope questions are declined

**Production monitoring (future):**
- Question volume and top queries
- User feedback ("was this answer helpful?")
- Manual audit of a sample per week

## Alternatives considered and rejected

### 1. Embedding-based retrieval (dense vectors)
- **Cost:** Embedding model + vector index (more infrastructure)
- **Latency:** Embedding call + vector search (still <1s, but slower than keyword)
- **Gain:** Handles synonyms better
- **Why rejected:** Keyword matching already works for this corpus; complexity not justified yet. *Revisit if recall@3 < 95% on test set.*

### 2. Multi-agent orchestration
- **Shape:** One agent per policy domain (leave, expenses, equipment, etc.)
- **Why rejected:** Overkill. Single agent with retrieval is simpler and cheaper. *Revisit only if a single agent becomes a bottleneck (unlikely).*

### 3. LLM-based retrieval ranking
- **Idea:** Use Claude to score which policies are relevant
- **Cost:** One extra LLM call per question
- **Why rejected:** Keyword scores are fast and work well enough. *Not cost-justified without evidence of retrieval failures.*

### 4. Full corpus in every prompt (no retrieval)
- **Approach:** Always include all 5 policies in the system prompt
- **Latency:** Single call, no retrieval overhead
- **Context:** ~2k tokens, well within budget
- **Why rejected:** No retrieval signal means Claude can't disambiguate ("is the user asking about leave or expenses?"). Keyword retrieval is a cheap way to clarify intent. *This was actually close; started with this, added retrieval to reduce hallucination.*

## Next steps

1. **Verify retrieval recall:** Test on 20 real employee questions. If recall@3 > 95%, ship as-is.
2. **Monitor production:** Track top questions, any "I don't know" answers, manual audits.
3. **Add multi-turn (if needed):** Only if employees frequently follow up with clarifications.
4. **Expand policies:** Add new policies to `policies/` dir; agent picks them up automatically.
5. **Upgrade to embeddings (if needed):** If keyword matching recall drops below 90% as corpus grows.

## Files

- `agent.py` — Main agent implementation (load policies, retrieve, call LLM, cite source)
- `llm.py` — Wrapper over Anthropic Messages API
- `test_agent.py` — Retrieval, answer quality, scope handling, end-to-end tests
- `policies/` — HR policy markdown files (new policies auto-picked up)
- `requirements.txt` — Dependencies
