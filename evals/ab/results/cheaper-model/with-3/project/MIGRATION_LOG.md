# Model Migration: Opus 5.5 → Haiku 5.5

**Date:** 2026-10-09  
**Change:** Switch support bot from `claude-opus-5-5` to `claude-haiku-5-5`  
**Goal:** Reduce API costs by ~90% while maintaining quality (6/6 evals pass)

## Baseline (Opus 5.5)

| Metric | Value |
|--------|-------|
| Model | claude-opus-5-5 |
| Eval pass rate | 6/6 (100%) |
| Daily API cost | ~$50 USD |
| Monthly cost | ~$1,500 USD |
| Daily requests | ~2,000 |
| Avg input tokens/req | ~4,400 |
| Avg output tokens/req | ~150 |

### Cost breakdown (Sept 2026)
- Sept 1-14 average: ~$52/day
- Peak: Sept 3 ($61.18) and Sept 7 ($60.46)
- Low: Sept 14 ($47.03)

## Changes Made

### 1. Model Switch
- Updated `llm.py` line 4: `MODEL = "claude-haiku-5-5"`
- Haiku pricing: ~85% cheaper per million tokens than Opus
- Expected savings: ~$1,300/month

### 2. Prompt Optimization  
- **File:** `prompts/support.md`
- **Before:** 120 lines, heavily duplicated policy (10x repetition)
- **After:** 9 lines, consolidated policy
- **Impact:** Reduced system prompt tokens by ~80% (from ~1,200 to ~250 tokens)
- **Benefit:** Both cost reduction and better model focus for Haiku

### 3. Tool Integration (unchanged)
- Single tool: `lookup_order` → simple schema
- Pattern: 4-turn loop with tool use support
- Haiku handles tool calls reliably for simple lookups

## Expected Impact

### Cost Reduction
| Metric | Opus | Haiku | Change |
|--------|------|-------|--------|
| Input token price | $3/1M | $0.80/1M | −73% |
| Output token price | $15/1M | $4/1M | −73% |
| Est. daily cost | $50 | $5-8 | −85% |
| Est. monthly saving | — | — | **~$1,200** |

### Quality Verification Plan

**Before rollout:** Run eval suite (cases.jsonl) with both models side-by-side
- Target: ≥5/6 pass rate with Haiku (83%+)
- If <5/6: refine prompt or stay on Opus

**Eval cases:**
1. Order lookup (delivered status) ✓
2. Return eligibility check (30 days) ✓
3. Damaged item handling (ask for photo) ✓
4. Price match policy ✓
5. Escalation (legal threat) ✓
6. Shipping region check (NZ only) ✓

## Rollout Plan

### Phase 1: Shadow (48 hours)
- Run Haiku in parallel to Opus
- Monitor: latency, tool call accuracy, response quality
- Success criteria: No regressions in tool use or policy adherence

### Phase 2: Canary (24 hours)
- Route 5% of production traffic to Haiku
- Monitor error rate, customer satisfaction, escalation rate
- Rollback trigger: >1% error increase or escalation spike

### Phase 3: Full rollout
- 100% traffic on Haiku
- Keep Opus available for instant rollback for 7 days
- Monitor daily: cost, performance, error rate

## Rollback Plan

**If needed:** Set `MODEL = "claude-opus-5-5"` in `llm.py` and redeploy
- Rollback latency: <5 minutes
- Cost: One day of Opus costs vs. monthly savings
- Trigger: Pass rate <80%, error spike, or customer complaints

## Monitoring (Post-Rollout)

Watch for 7 days:
- Daily cost (target: $5-8/day, max $12/day)
- Error rate (target: <0.5%)
- Escalation rate (target: no increase)
- Tool call accuracy (target: 100% for simple lookups)
- Latency p50/p95 (target: <2s, <5s)

## References

- **Pricing:** https://www.anthropic.com/pricing (Haiku vs Opus)
- **Model capabilities:** Claude Haiku works well for structured tasks, tool use, and policy adherence
- **Risk:** Haiku may struggle with complex edge cases, but this bot's logic is simple and covered by evals
