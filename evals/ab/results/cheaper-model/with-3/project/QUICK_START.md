# Quick Start: Deploy Haiku Migration

## TL;DR
- **Saves:** ~$1,250/month (~85% cost reduction)
- **Change:** Opus 5.5 → Haiku 5.5
- **Risk:** Low (eval-gated, canary rollout)
- **Status:** ✅ Ready to deploy

## Files Changed
```
llm.py                          → MODEL = "claude-haiku-5-5"
prompts/support.md              → Consolidated 120→9 lines
evals/run_eval.py               → Fixed imports
tests/test_model_migration.py    → NEW: Eval comparison tool
MIGRATION_LOG.md                → NEW: Detailed plan
DEPLOYMENT.md                   → NEW: Rollout procedure
COST_REDUCTION_SUMMARY.md       → NEW: Executive summary
CHANGES_OVERVIEW.txt            → NEW: This overview
```

## 3 Paths Forward

### Fast Path (Trust the analysis)
1. Review COST_REDUCTION_SUMMARY.md
2. Merge changes
3. Deploy to staging
4. Follow DEPLOYMENT.md (shadow → canary → full)

### Safe Path (Validate first)
1. `export ANTHROPIC_API_KEY=your-key`
2. `export MODEL=claude-opus-5-5 && python evals/run_eval.py`  (baseline)
3. `export MODEL=claude-haiku-5-5 && python evals/run_eval.py` (candidate)
4. If ≥5/6 pass → proceed as Fast Path

### Cautious Path (Extended testing)
1. Deploy to staging only
2. Run shadow test for 48 hours
3. Review logs, costs, errors
4. Decision point: proceed or refine

## Key Metrics

| Metric | Before | After | Notes |
|--------|--------|-------|-------|
| Model | Opus 5.5 | Haiku 5.5 | 73% cheaper/token |
| Daily cost | $50 | $5-8 | 85% reduction |
| Monthly cost | $1,500 | $200-250 | $1,250 savings |
| Eval pass | 6/6 | ≥5/6 | Target: ≥83% |
| Risk | — | LOW | Canary + rollback |

## Rollback (if needed)
```bash
# Instant revert
git checkout llm.py prompts/support.md
# Or: export MODEL=claude-opus-5-5
# Redeploy: <5 minutes
```

## Monitoring After Deploy

Watch for 7 days:
- Daily cost → target: $5-8 USD
- Error rate → target: <0.5%
- Escalations → target: no change
- Tool calls → target: 100% success

## Questions?

- **Technical details:** See MIGRATION_LOG.md
- **Deployment steps:** See DEPLOYMENT.md
- **Full analysis:** See COST_REDUCTION_SUMMARY.md
- **Code changes:** `git diff`

---
Ready to proceed? Start with COST_REDUCTION_SUMMARY.md, then DEPLOYMENT.md.
