# Conversation and handoff

Record these choices (Scope and HITL sections of `design.md` if used).

## Clarify or proceed

Ask only when the answer changes what the agent does **and** a wrong guess is costly.

| Situation | Do |
|---|---|
| Missing detail a tool can discover | Look it up; don't ask |
| Ambiguous intent, reversible or read-only action | Proceed on the most reasonable assumption, state it in one line, offer to redo |
| Ambiguous intent, irreversible, money, external message, shared system | Ask first, with options spelled out |
| Several readings with very different cost or scope | One question with 2–3 choices, not "what do you mean?" |
| Input only the user has (account to charge, recipient) | Ask; never invent it |
| Long or costly underspecified task | Plan-then-execute (`workflow-patterns.md`), questions in the plan |

- Batch questions into one turn.
- State assumptions where the user sees them: "Assumed the EU price list; say if you meant US."
- Set the default in the prompt: either "infer the most useful action and proceed, using
  tools to discover missing details" or "research and recommend; act only on explicit
  request". Pick one per agent (`agent-prompting`).
- Gate risky tools in code (`agent-guardrails`); the model asking isn't the control.
- Intent still unclear after a few attempts → escalate, don't keep asking.

## Refusals and out-of-scope

- Decide scope in design, enforce in code: route out-of-scope intents with rules or a small
  classifier before the main model; hard-code the reply where you can.
- One sentence on what you can't do, one on what you can or where to go. No lecture.

```text
I can't change billing details from here. I can explain this invoice line by line,
or connect you to the billing team, who can update it. Which would help?
```

- Separate "won't" (policy) from "can't" (no access) so the user knows if a human can help.
- Over-refusal is a failure: add borderline in-scope cases to the eval set and track the
  false-refusal rate (`agent-evals`).
- Dependency down: answering from model knowledge when retrieval fails is a business call;
  critical use cases should refuse. LLM down → a clear error.

## Progress on long tasks

- Open by restating the goal and plan, then act, so a misread task can be stopped early.
- One line per completed phase, not per call. Finish with what was done, what changed, what
  is left, as plain facts.
- Make every step inspectable (files touched, tools called) in a details view.
- Stream long answers. Report blockers at once with what was tried. Unattended runs send a
  status and a link, not a transcript.

## Handing off to a human

Triggers (record which): user asks for a person; intent unclear after a few attempts;
high-risk action; low confidence; repeated tool failures (`agent-production` →
`references/reliability.md`); distress, complaints, scoped-out legal topics. With a
calibrated classifier: act on high confidence for reversible actions, gather context and
retry (finite) on medium, escalate on low.

| Handoff | Shape | Use when |
|---|---|---|
| Warm | Agent stays until a human joins, passes a brief, human takes the live conversation | Live chat/voice with staff available; upset or high-value users |
| Cold | Agent files a ticket with the brief and tells the user what happens next and when | No one available; async channels |

Pass a brief, not just a transcript, so the human re-asks nothing:

```text
Reason for handoff:  <trigger, e.g. refund above agent limit>
User and account:    <verified identity, plan, language>
Goal:                <what the user wants, one line>
Done so far:         <steps taken, tool results, what failed>
Pending / proposed:  <action awaiting approval, exact arguments>
Sentiment / urgency: <if relevant>
Transcript:          <link>
```

- Tell the user every time: a person is taking over, roughly when, whether to stay. Never let
  a human silently impersonate the agent, or vice versa.
- Once handed off, the agent stops acting; it may draft for the human but doesn't send.
- Measure handoff rate per trigger, time to human, resolution after handoff. A rising rate
  for one intent is a design or tooling gap (`agent-observability`).
