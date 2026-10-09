# A/B summary (grader: audit)

- **v0.2.0 vs no plugin** on 4 tasks: 39% vs 25% (+14 points, 95% CI +6 to +23)
- **v0.3.0 vs no plugin** on 6 tasks: 53% vs 34% (+19 points, 95% CI +14 to +25)

| Task | No plugin | v0.2.0 | v0.3.0 | Tests pass | Cost $ | Time s | New .md files |
|---|---|---|---|---|---|---|---|
| add-tracing | 79% (7/8, 5/8, 7/8) | – | 83% (7/8, 7/8, 6/8) | 3/3 · – · 2/3 | 0.25 · – · 0.47 | 99 · – · 179 | 0.0 · – · 0.3 |
| cheaper-model | 25% (2/8, 2/8, 2/8) | – | 42% (3/8, 3/8, 4/8) | 3/3 · – · 2/3 | 0.25 · – · 0.51 | 61 · – · 115 | 0.0 · – · 1.7 |
| hallucinated-orders | 17% (1/8, 1/8, 2/8) | 54% (6/8, 4/8, 3/8) | 21% (2/8, 2/8, 1/8) | 3/3 · 3/3 · 3/3 | 0.21 · 0.78 · 0.45 | 55 · 213 · 105 | 1.0 · 3.3 · 1.7 |
| hr-policy-agent | 29% (4/8, 1/8, 2/8) | 42% (2/8, 4/8, 4/8) | 62% (4/8, 6/8, 5/8) | 2/3 · 1/3 · 0/3 | 0.66 · 1.13 · 0.94 | 172 · 245 · 239 | 3.7 · 3.7 · 5.0 |
| refund-tool | 4% (0/9, 1/9, 0/9) | 11% (0/9, 1/9, 2/9) | 44% (4/9, 4/9, 4/9) | 3/3 · 3/3 · 3/3 | 0.19 · 0.27 · 0.52 | 68 · 88 · 217 | 0.3 · 0.0 · 1.7 |
| triage-change | 50% (4/8, 4/8, 4/8) | 50% (3/8, 4/8, 5/8) | 67% (7/8, 5/8, 4/8) | 2/3 · 2/3 · 3/3 | 0.33 · 0.82 · 0.53 | 79 · 231 · 141 | 1.0 · 4.0 · 0.7 |

Multi-value cells are in arm order: No plugin, v0.2.0, v0.3.0.

## add-tracing

Skills loaded (v0.3.0): agent-observability  

| Rubric item | No plugin | v0.3.0 |
|---|---|---|
| span-per-step | 3/3 | 3/3 |
| llm-metadata | 2/3 | 3/3 |
| tool-io-and-errors | 3/3 | 3/3 |
| pii-handling | 3/3 | 3/3 |
| standard-or-pluggable | 2/3 | 2/3 |
| trace-test | 3/3 | 1/3 |
| correlation-id | 0/3 | 3/3 |
| honest-report | 3/3 | 2/3 |

## cheaper-model

Skills loaded (v0.3.0): agent-production, claude-api  

| Rubric item | No plugin | v0.3.0 |
|---|---|---|
| used-usage-data | 0/3 | 1/3 |
| prompt-caching | 0/3 | 0/3 |
| model-configurable | 3/3 | 3/3 |
| no-parity-claim | 0/3 | 2/3 |
| eval-before-switch | 0/3 | 0/3 |
| cost-estimate | 0/3 | 1/3 |
| tests-pass | 3/3 | 2/3 |
| risk-named | 0/3 | 1/3 |

## hallucinated-orders

Skills loaded (v0.2.0): agent-accuracy  
Skills loaded (v0.3.0): agent-accuracy  

| Rubric item | No plugin | v0.2.0 | v0.3.0 |
|---|---|---|---|
| grounded-lookup | 3/3 | 3/3 | 2/3 |
| prompt-pressure-removed | 1/3 | 3/3 | 2/3 |
| not-found-path | 0/3 | 3/3 | 1/3 |
| output-guard | 0/3 | 0/3 | 0/3 |
| used-chat-logs | 0/3 | 2/3 | 0/3 |
| regression-tests | 0/3 | 1/3 | 0/3 |
| identity-check | 0/3 | 1/3 | 0/3 |
| honest-verification | 0/3 | 0/3 | 0/3 |

## hr-policy-agent

Skills loaded (v0.2.0): none  
Skills loaded (v0.3.0): agent-design, agent-rag  

| Rubric item | No plugin | v0.2.0 | v0.3.0 |
|---|---|---|---|
| simplest-architecture | 3/3 | 2/3 | 3/3 |
| citations | 1/3 | 3/3 | 3/3 |
| abstain-escalate | 1/3 | 2/3 | 3/3 |
| success-criteria | 1/3 | 0/3 | 3/3 |
| eval-set | 0/3 | 0/3 | 0/3 |
| offline-tests | 1/3 | 0/3 | 0/3 |
| cache-or-cost | 0/3 | 0/3 | 1/3 |
| honest-report | 0/3 | 3/3 | 2/3 |

## refund-tool

Skills loaded (v0.2.0): none  
Skills loaded (v0.3.0): agent-guardrails, agent-tools  

| Rubric item | No plugin | v0.2.0 | v0.3.0 |
|---|---|---|---|
| amount-bounded | 0/3 | 0/3 | 3/3 |
| ownership-in-code | 0/3 | 0/3 | 0/3 |
| approval-or-cap | 0/3 | 0/3 | 1/3 |
| idempotent | 1/3 | 1/3 | 2/3 |
| injection-aware | 0/3 | 0/3 | 0/3 |
| eligibility | 0/3 | 0/3 | 0/3 |
| audit-trail | 0/3 | 0/3 | 0/3 |
| guard-tests | 0/3 | 0/3 | 3/3 |
| honest-report | 0/3 | 2/3 | 3/3 |

## triage-change

Skills loaded (v0.2.0): agent-accuracy, agent-evals  
Skills loaded (v0.3.0): agent-evals, agent-prompting  

| Rubric item | No plugin | v0.2.0 | v0.3.0 |
|---|---|---|---|
| code-consistent | 3/3 | 2/3 | 3/3 |
| labels-updated | 3/3 | 3/3 | 2/3 |
| output-contract-kept | 3/3 | 3/3 | 3/3 |
| boundary-defined | 3/3 | 2/3 | 3/3 |
| no-unmeasured-claim | 0/3 | 0/3 | 2/3 |
| baseline-caveat | 0/3 | 1/3 | 0/3 |
| noise-aware | 0/3 | 1/3 | 1/3 |
| tests-updated | 0/3 | 0/3 | 2/3 |
