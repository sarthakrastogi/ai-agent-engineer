# Input and output guards

## Layers

| Layer | Runs on | Checks | Implementation |
|---|---|---|---|
| Input | First agent's input | Topic, jailbreak/injection signals, PII, length, rate | Small classifier, regex, rules |
| Retrieved / tool content | Each tool result | Injection signals, size, PII | Classifier, truncation, redaction |
| Tool call | Every call, before execution | Schema, authz, caps, allowlists, argument provenance | Code (`approvals-and-permissions.md`) |
| Output | Last agent's output | Schema, moderation, grounding, PII/secret scan, URL and markdown sanitisation | Validators, classifier, LLM judge for subjective checks |

Add guards from failures seen in traces and red-teaming, not from a generic list. Order
cheapest first: rules/regex → detector → rate limits → output validation → approval on
critical actions. Keyword rules alone are brittle; keep them as a layer only.

## Blocking vs parallel

- **Before any side effect: blocking.** Tool-call guards always block; a parallel guard
  trips after tools already ran.
- Pure text generation: parallel is fine; discard output if the guard trips.
- Streaming: buffer until output checks pass, or accept retracting visible text.

## Using classifiers

- Attackers retry and adapt to the specific classifier; published robustness is against
  static sets.
- Measure false positives on benign production traffic before blocking — refusing 3% of
  real users is a product bug. At 1% attack prevalence, a 5% benign error rate flags ~5
  legitimate users per attacker.
- Validate each guard like a judge: labelled set, TPR/TNR, re-check after model or prompt
  changes (`agent-evals`).
- Small fine-tuned classifiers beat LLM calls on latency but generalise poorly outside
  their training domain. A detector trained on user prompts is unvalidated on tool
  results, documents and emails until tested there.
- **Sabotage-test every guard** in testing and after each deploy
  (`agent-observability` → `references/instrumentation-health.md`).
- **Fail-open vs fail-closed is a per-guard business decision with the user.** Fail open
  only where the guard isn't the boundary (privilege and caps still hold), with an alert;
  fail closed in front of high-risk tools. Run guard models as separate services with
  their own memory limit behind a circuit breaker (`agent-production` →
  `references/reliability.md`).
- Off-the-shelf options (moderation APIs, open guard models, injection classifiers): pick
  by measured TPR/FPR on your data, not benchmark claims.

## Small inline detectors

An encoder classifier with no decoding is cheap enough to run **blocking** in front of
every LLM call — better than an LLM guard in parallel. It cuts attack volume and makes
attempts visible; it doesn't replace architecture.

- **Shape:** mid-size encoder (e.g. ModernBERT-large) embedding + small feed-forward binary
  head, contrastive loss (benign pulled together, malicious pushed apart). Runs on CPU.
  Plain encoder classifiers handle clean inputs but miss subtle adversarial ones; small
  generative guards do better but are heavier and generalise poorly across attack types.
- **Data:** every attack category you care about, plus benign traffic like yours — real
  logged queries over LLM-generated ones (synthetic lacks your users' borderline phrasing).
- **Hard negatives in train and eval:** harmless queries containing attack phrases ("what
  is a system prompt?", "my teacher said to ignore previous instructions"). Without them
  the guard keys on words.
- **Generative guard:** start from the instruct model, not base (label-only SFT on base
  tends to call everything malicious); one sentence of rationale before the label improves
  edge cases and cuts false positives; check the predicted-class distribution, not only
  accuracy.
- **Read headline numbers honestly:** 95% on the builder's static benchmark is not recall
  against adaptive attackers and says nothing about FPR.
- **Tiers to start, then calibrate:** confidence > 0.8 → block; 0.5–0.8 → flag for review.
  "Extra constraints" means fewer tools or a stricter approval tier for that request,
  never extra prompt wording.
- **On a flag:** block, log, or review. A rewriter model must be tool-less and its output
  untrusted — it has read the attack.

## Output handling

Treat model output as user input arriving at the next system:

- **SQL:** parameterised queries or a builder; prefer constrained tools
  (`get_orders(customer_id, since)`) over free SQL.
- **Shell:** argument arrays, allowlisted binaries; no string-built commands.
- **HTML/markdown:** escape by default; no auto-rendered external images; allowlist link
  domains; strict CSP.
- **URLs:** validate scheme and host against an allowlist before fetch or render.
- **Structured output:** validate against the schema in code even with strict modes;
  reject or repair.
- **Code:** execute only in a sandbox. For agents that ship code, make security scanning
  a loop step before a change is accepted — access policies (e.g. row-level security),
  code, auth flows, dependencies — and feed findings back as errors to fix.
- UX: show sources, make outputs easy to dismiss or edit, label AI-generated content.

## PII

- **Minimise:** don't fetch unneeded fields; tools return masked values (`****1234`) by
  default, with a separate gated tool for full values.
- **Keep PII out of the model where possible:** process in code and tokenise so only
  placeholders pass through; the executor substitutes real values at the sink.
- **When the task needs the value** (phone number + OTP for a plan change), tokenise or
  pass it through, but still scrub logs and traces. Infer which fields the task needs; state
  it.
- Redact before logging/tracing (`agent-observability` →
  `references/content-capture-pii-sampling.md`).
- Ask about residency, provider data-retention settings, and retention for traces and
  memories; don't assume defaults comply.
- No PII in long-term memory without a deletion path.
- PII detectors (e.g. Presidio) miss context-dependent PII; treat as a layer.

## Secrets

- Never in prompts, tool descriptions or context; assume the system prompt is extractable.
- Inject credentials in the executor; return results, never credentials.
- **Detect secrets on input:** a key pasted into chat goes to the secret manager and is
  referenced by name, never echoed into code or context.
- **Publishable vs privileged keys, enforced by the harness:** client-safe keys may appear
  in front-end code; privileged keys live only server-side, loaded from the secret store.
- No secrets in sandbox environments, eval datasets or traces (the pack's `secret-guard`
  hook blocks likely keys in repo writes).
- Scan outputs and tool arguments for key patterns (cloud keys, tokens, private-key
  headers) and block on match.
- **Leaked secret:** revoke immediately, issue a new one, update the app, check for
  unauthorised use. Deleting the commit or trace is not remediation.
