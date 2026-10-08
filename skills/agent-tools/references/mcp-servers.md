# MCP servers

An MCP server is still a tool set: every rule in `tool-definition-checklist.md` and
`tool-responses-and-errors.md` applies. Verify field names against the current MCP spec.

## When to use MCP

| Situation | Choose |
|---|---|
| Tools used by one app you control | Native function tools |
| Same tools across several agents, apps or harnesses (IDE, chat, CI) | MCP server |
| Internal system exposed to many teams' agents | Remote MCP server with OAuth |
| A mature CLI exists and the agent has a sandboxed shell | The CLI may cost less context |
| Bulk processing across many tool results | Code execution over MCP tools, intermediates out of context |

Don't auto-generate one tool per OpenAPI operation. Many clients support tools far better
than resources or prompts; check your target clients before relying on them.

## Server tool design

- **Names:** verb_object and distinctive enough to survive mixing with other servers' tools;
  avoid generic `search`, `get`.
- **`outputSchema` + `structuredContent`** when clients consume results programmatically;
  still return a readable text rendering.
- **Annotations** (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`): set
  them accurately. Clients treat annotations from untrusted servers as hints, never security;
  enforce risk in your own gate.
- **Errors:** tool failures as results with `isError: true` and an actionable message;
  protocol errors only for protocol problems.
- **Stable tool list:** don't rely on `listChanged` mid-session; keep a fixed list and check
  server-side what the current user may call.
- **Bounded results:** never stream unbounded output back as one tool result.

## Client-side efficiency

- Connect only the servers a given agent needs; each adds definitions and overlap.
- Many servers → tool search (`tool-definition-checklist.md` §1 Counts).
- Present MCP tools as code callable from a sandbox for bulk work, so intermediates and PII
  never transit the model.

## Transports and deployment

- **stdio** for local servers launched by the client; **Streamable HTTP** for remote.
- Local servers run with the user's privileges; sandbox them (`agent-guardrails`).
- Version the server. Any change to a tool name, description or schema is a behaviour change
  for every consuming agent: re-run their evals.

## Security

MCP auth and trust rules (no token passthrough, OAuth consent, redirect and state checks,
SSRF, provenance, pinning, tool poisoning, cross-server trifecta) live in `agent-guardrails` →
`references/approvals-and-permissions.md`. Server-design additions:

- Bind sessions to the user (`<user_id>:<session_id>`) so a leaked session ID can't act for
  someone else.
- Authorise against the end user's identity from the validated token, never from a tool
  argument or the model's request.

## Testing a server

1. Exercise it in the MCP Inspector: list tools, call each with valid and invalid input,
   check errors and output sizes.
2. Run the agent testing loop (`tool-definition-checklist.md` §7) with the target agent.
3. Test alongside the other servers the agent will have, to catch name and purpose overlap.
4. Test auth failures: expired token, wrong audience, user without permission.
