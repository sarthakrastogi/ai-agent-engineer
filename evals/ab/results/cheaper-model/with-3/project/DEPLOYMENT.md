# Deployment Guide: Haiku Model Switch

## Pre-Deployment Checklist

- [ ] Run eval suite with Haiku locally (see below)
- [ ] Verify ≥80% pass rate on cases.jsonl
- [ ] Review MIGRATION_LOG.md for impact analysis
- [ ] Get approval from ops/product team
- [ ] Have rollback procedure ready (see Rollback section)
- [ ] Alert monitoring team to watch dashboards

## Local Testing Before Rollout

### 1. Test with Opus (baseline)
```bash
export MODEL=claude-opus-5-5
export ANTHROPIC_API_KEY=<your-key>
python -m pytest tests/test_model_migration.py -v
```
Expected: 6/6 pass (100%)

### 2. Test with Haiku (candidate)
```bash
export MODEL=claude-haiku-5-5
export ANTHROPIC_API_KEY=<your-key>
python -m pytest tests/test_model_migration.py -v
```
Expected: ≥5/6 pass (≥83%)

### 3. Run full eval
```bash
cd evals
python run_eval.py
```
Compare output between runs.

## Deployment Steps

### Immediate (Phase 1: Shadow - 48 hours)

1. **Create feature branch:**
   ```bash
   git checkout -b feature/haiku-migration
   git pull origin main
   ```

2. **Verify changes:**
   ```bash
   git diff origin/main
   ```
   Should show:
   - `llm.py`: MODEL change to haiku-5-5
   - `prompts/support.md`: Prompt consolidation (80% smaller)

3. **Test once more:**
   ```bash
   MODEL=claude-haiku-5-5 python -m pytest tests/ -v
   ```

4. **Commit and PR:**
   ```bash
   git add -A
   git commit -m "Migrate support bot to claude-haiku-5-5

   - Switch from Opus to Haiku for 85% cost reduction (~$1,200/month)
   - Consolidate duplicated system prompt (120 → 9 lines)
   - Expected daily cost: $5-8 USD vs. $50 USD
   - Eval pass rate: 6/6 with Opus, ≥5/6 with Haiku
   - Rollout plan: shadow 48h → canary 24h → full with rollback

   See MIGRATION_LOG.md and DEPLOYMENT.md for details."
   git push origin feature/haiku-migration
   ```

5. **PR review and merge to develop/staging**
   - Notify team of rollout plan in PR description
   - Deploy to staging environment

6. **Run shadow test (48 hours):**
   - Deploy code to staging/shadow
   - Route 100% traffic through shadow (don't count cost)
   - Run normal volume tests
   - Monitor: latency, errors, tool use accuracy
   - Check logs for any policy violations or edge cases

### 24-Hour Test (Phase 2: Canary - 24 hours)

7. **Deploy to production (5% traffic):**
   - Use deployment configuration to route 5% of traffic to Haiku
   - Monitor closely:
     ```
     Dashboards to watch:
     - Error rate (alert if >1% for Haiku vs Opus baseline)
     - Response latency p50/p95 (alert if p95 > 5s)
     - Escalation rate (alert if increase >10%)
     - Tool call failures (alert if >0.1%)
     - API cost (expect ~$2.50/day for 5% traffic)
     ```

8. **Decision point (24 hours in):**
   - **Go:** ≥95% success rate → proceed to 100%
   - **Hold:** Review logs, refine if needed, extend canary
   - **Rollback:** <95% success or error spike

### Full Rollout (Phase 3: 100% traffic)

9. **Expand to 100% traffic:**
   - Gradual: 5% → 25% → 50% → 100% over 4-8 hours
   - Or direct if canary is stable

10. **Monitor for 7 days:**
    - Daily cost should stabilize at $5-8 USD/day
    - Maintain <0.5% error rate
    - No escalation spike

## Rollback Procedure

### Immediate Rollback (if issues detected)

1. **Switch back to Opus:**
   ```bash
   git checkout main
   git pull origin main
   # Or temporarily set MODEL=claude-opus-5-5 if already deployed
   ```

2. **Redeploy:**
   ```bash
   # Via your standard deployment pipeline
   # Rollback should complete in <5 minutes
   ```

3. **Verify:**
   ```bash
   curl https://api.yourservice.com/health
   # Check dashboard: error rate should drop immediately
   ```

4. **Post-mortem:**
   - Review logs from Haiku period
   - Document what failed
   - Adjust prompt/tool design if needed
   - Schedule retry

### Gradual Rollback (if subtle degradation)

- If issues are gradual, drain traffic from Haiku first:
  - 100% → 50% → 25% → 5% → 0% over 2-4 hours
  - Switch to Opus once at 0%

## Cost Tracking

### Before (Opus baseline)
```
Monthly cost: ~$1,500 USD
Daily average: ~$50 USD
Peak: ~$61 USD (Sept 3)
```

### Expected after (Haiku target)
```
Monthly cost: ~$200-250 USD
Daily average: ~$5-8 USD
Savings: ~$1,250/month
```

### Post-rollout verification
- [ ] Verify daily cost hits $5-8 range within first 3 days
- [ ] If not, review:
  - Tool call patterns (loops?)
  - Response length (truncation?)
  - Error handling (retries?)
  - Load patterns (unexpected spike?)

## Monitoring & Alerting

Create alerts for:
- **Cost anomaly:** Daily cost > $12 USD (1.5x expected)
- **Error rate spike:** Error rate > 1% for Haiku
- **Escalation rate:** Increase > 10% vs baseline
- **Tool failures:** Any tool_use_id without result
- **Latency:** p95 > 5 seconds

## Communication

- [ ] Notify support team: Haiku deployment planned
- [ ] Notify finance: Cost reduction of ~$1,250/month starting [date]
- [ ] Notify ops: Rollback procedures, alert setup
- [ ] Post-mortem: After 7 days, document actual vs. predicted costs

## Success Criteria

✅ **Deployment is successful if:**
1. Pass rate ≥80% (5/6 eval cases) with Haiku
2. Error rate <0.5% in canary/production
3. No escalation spike (legal/safety cases handled correctly)
4. Daily cost $5-8 USD (target) by day 3
5. p95 latency ≤5 seconds (same as Opus)
6. No customer complaints in first 7 days

❌ **Rollback if:**
1. Pass rate <80% (<5/6)
2. Error rate >1%
3. Escalation rate increases >10%
4. Daily cost >$15 USD (unexpected)
5. p95 latency >8 seconds
6. Significant customer complaints

---

**Owner:** [Your name]  
**Created:** 2026-10-09  
**Last updated:** 2026-10-09
