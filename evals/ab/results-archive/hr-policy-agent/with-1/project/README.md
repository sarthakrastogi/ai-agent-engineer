# HR Policy Agent

A Python agent that answers employee questions about company HR policies using Claude.

## Overview

This is a simple, single-call LLM agent that:
- Loads HR policies from markdown files in `policies/`
- Embeds all policies in the system prompt
- Answers employee questions accurately and with proper citations
- Refuses to invent policies not in the official documentation

## Architecture

**Design choice: Single LLM call with full context**

We chose this over an agent loop because:
- Policies are fixed and don't change mid-conversation
- Each question has a clear, single answer
- No multi-turn reasoning or tool failures to recover from
- All policies (~2KB) fit easily in the prompt

This is the simplest architecture that meets the requirements.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

## Usage

### From the command line

Ask a single question:
```bash
python agent.py "How much annual leave do I get?"
```

Interactive mode:
```bash
python agent.py
# Then type your question at the prompt
```

### In Python code

```python
from agent import answer_question

answer = answer_question("What's my meal allowance while travelling?")
print(answer)
```

## Testing

Run the test suite:
```bash
pytest test_agent.py -v
```

Tests verify:
- Policies load correctly
- Agent answers include relevant policy citations
- Agent acknowledges when policies don't cover a question

## Policy files

Policies are stored in `policies/` as markdown:
- `leave.md` — Annual leave, sick leave, parental leave
- `remote-work.md` — Work-from-home and overseas work rules
- `travel.md` — Flight booking, approval requirements
- `equipment.md` — Laptop refresh cycle, device security
- `expenses.md` — Claim submission, spending limits, approvals

## How the agent works

1. **Load policies** — All markdown files in `policies/` are loaded
2. **Build system prompt** — Policies are embedded with instructions to cite them accurately
3. **Answer question** — Single API call to Claude with the question and all policies in context
4. **Return answer** — Direct, cited response with no hallucinations

## Key principles

- **No synthesis** — The agent only answers from the provided policies
- **Always cite** — Every answer includes which policy section it came from
- **Acknowledge gaps** — If a question isn't covered, the agent says so explicitly
- **Single call** — Fast and predictable; no loops or retries needed

## Extending the agent

If you want to add more capabilities:

- **More tools** — Use the `agent-tools` skill to add tools (e.g., "submit a leave request")
- **Multi-turn conversation** — Modify `answer_question()` to keep a message history
- **Semantic search** — If policies grow large, add vector retrieval (see `agent-rag`)
