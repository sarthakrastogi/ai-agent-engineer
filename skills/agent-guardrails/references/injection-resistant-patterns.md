# Injection-resistant design patterns

Once the agent has ingested untrusted input, that input must be unable to trigger any
consequential action. Each pattern trades flexibility for that guarantee; pick the least
flexible one that does the job.

Detection-style defences (classifiers, delimiters, spotlighting, instruction-hierarchy
training, prompt reminders) cut attack rates but never to zero, and adaptive attackers beat
static-benchmark numbers by far. Layer them on a pattern, never instead of one.

## Choosing

| Pattern | Flexibility | Guarantee | Best fit |
|---|---|---|---|
| Action-selector | Lowest | Tool output never reaches the model | Routers, command front-ends, menus |
| Plan-then-execute | Low | No *new* actions from injected data; arguments can still be steered | Email/calendar assistants, fixed multi-step tasks |
| LLM map-reduce | Medium | Each reader's output constrained; one poisoned doc affects only its value | Bulk triage, extraction over many files |
| Dual LLM | Medium-high | Privileged model never sees untrusted text | Assistants acting on data they summarise |
| Code-then-execute / CaMeL | High | Deterministic policy on every sink, with provenance | General agents with tools and untrusted data |
| Context minimisation | Any | Removes injection from later turns | Any agent where the user prompt is the main risk |

Patterns compose with least privilege and approvals; they don't replace them.

## 1. Action-selector

The model maps the request to one of a fixed set of actions and never sees results; tool
output goes straight to the user. Cost: no multi-step reasoning over results.

## 2. Plan-then-execute

Commit the full sequence of calls from the trusted request *before* reading untrusted
content. Untrusted data can fill arguments but can't add calls.

```text
plan = llm_plan(user_request, tool_specs)         # sees only trusted input
validate(plan)                                     # code: allowed tools, targets, limits
for step in plan:
    result = execute(step, args=resolve(step, previous_results))
```

- Injected content can still steer *what* a fixed call does. Fix recipients/targets from
  the trusted request and check sink-call arguments.
- The plan is a natural single approval point.
- **Two-mode variant:** a planning mode whose tool set has no write tools (enforced by the
  executor, not by instruction); write tools appear only after the user approves the plan.
  If planning reads untrusted content, the plan itself can be steered — this limits
  damage but doesn't give the guarantee.

## 3. LLM map-reduce

One tool-less reader call per untrusted item, returning a **constrained** value (bool,
enum, number, or schema-validated record with no free text). The reducer — code or a
privileged model — sees only those values.

```text
flags = [reader(doc, schema={"contains_invoice": bool, "amount": float}) for doc in docs]
total = sum(f.amount for f in flags if f.contains_invoice)   # code, not a model
```

The constraint is the defence: a free-text field re-injects the document. Validate every
reader output in code; drop or flag on failure.

## 4. Dual LLM

A **privileged** model plans and calls tools but never reads untrusted text. A
**quarantined** model reads it, has no tools, and returns results stored as handles
(`$VAR1`). Code substitutes real values only at display or at a policy-allowed sink.
Judgement over untrusted text requires the quarantined model to return constrained values.

## 5. Code-then-execute / CaMeL

The privileged model writes a program in a restricted language that calls tools and a
quarantined parser model. The interpreter tags every value with provenance and allowed
recipients; a policy checks argument provenance before each tool call.

```text
def before_tool_call(call):
    if call.tool in SINKS and any(UNTRUSTED in a.sources for a in call.args):
        return require_user_approval(call)       # or deny
    if call.tool == "send_email" and not recipient_trusted(call.args["to"]):
        return deny("recipient not from trusted input")
    return allow()
```

- Guarantees hold however the model is fooled. Costs: policy maintenance, an interpreter
  or taint layer, approval fatigue if policies are coarse, some task-success loss —
  measure it on your eval set.
- **Lighter version most teams can build:** tag values `source ∈ {user, system, untrusted}`
  in the tool layer, propagate through your code, enforce sink policies in the executor.
  Treat anything the model emits after reading untrusted data as untrusted.

## 6. Context minimisation

Drop content once it has served its purpose: turn the request into a structured query, run
it, show results without re-feeding the original prompt; clear untrusted tool results after
extracting values (`agent-context` for tool-result clearing).

## Output-side companions

Close the exfil leg regardless of pattern:

- Don't auto-render images from model output; if required, proxy and allowlist hosts.
- Allowlist link domains; show full URLs, not anchor text.
- Restrict fetch tools to allowlisted domains, or strip model-composed query strings.
- Fix recipients, repos and channels from trusted input; the model doesn't choose.
