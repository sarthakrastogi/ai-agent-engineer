# HR Policy Agent

A conversational agent that answers employee questions about company HR policies with citations.

## Features

- **Policy-based answers**: All responses are grounded in the HR policies in the `policies/` directory
- **Multi-turn conversation**: Maintains context across follow-up questions
- **Prompt caching**: Uses Anthropic's prompt caching for efficient, cost-effective repeated queries
- **Citations**: Tells you which policy document each answer came from
- **Interactive mode**: Chat naturally with the agent, or ask single questions via CLI

## Setup

```bash
pip install -r requirements.txt
```

Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY=your-key-here
```

## Usage

### Interactive mode (multi-turn conversation)

```bash
python hr_agent.py
```

Then ask questions naturally:
```
Your question: How many days of annual leave do I get?
Assistant: [answer with citation]

Your question: Can I carry days over to next year?
Assistant: [answer with citation]
```

### Single question from CLI

```bash
python hr_agent.py "What is the remote work policy?"
```

### Test the agent

```bash
python test_agent.py
```

This runs the agent through a series of typical employee questions to verify it's working correctly.

## Policies

The agent loads all `.md` files from the `policies/` directory:
- `leave.md` - Annual leave, sick leave, parental leave
- `expenses.md` - Expense claims, reimbursement limits, approval processes
- `remote-work.md` - Remote work allowances and approvals
- `travel.md` - Travel booking and class requirements
- `equipment.md` - Laptop refresh cycles and security policies

## Design

This agent uses a **single-call + prompt caching** architecture:
- All policies (~3KB) fit comfortably in the prompt context
- Prompt caching reduces latency and cost on repeated queries
- No agent loops needed: policies are deterministic reference material
- Claude bases all answers strictly on provided policies

### Why not a vector database?

For small, stable policy documents:
- Prompt + caching is faster (no retrieval step)
- Cheaper (fewer API calls, cache reuse)
- Simpler (no indexing or embedding overhead)
- More accurate (Claude sees all context at once)

### Why a single LLM call?

- No intermediate decisions needed
- Policies are complete in one context window
- Multi-turn is handled via conversation history, not agentic loops
- Simpler, more predictable, lower cost

## Cost & Performance

- **First query**: ~1-2 seconds, full context cost
- **Subsequent queries**: <500ms, ~10% context cost (via prompt cache)
- **Monthly estimate** (500 queries): ~$0.30-0.50

(Estimates based on Claude 3.5 Sonnet pricing; see Anthropic docs for current rates)

## Extending the agent

To add new HR policies:
1. Create a new `.md` file in the `policies/` directory
2. Use standard markdown with clear section headers
3. Re-run the agent—it auto-discovers all `.md` files

To change the system prompt tone or behavior:
- Edit the `create_system_prompt()` function in `hr_agent.py`
- Adjust the instructions as needed (keep policies in context)

## Limitations

- Only answers questions covered by the provided policies
- Does not make decisions or judgements (e.g., "Is my situation eligible?")
- Does not interact with payroll, HR systems, or external APIs
- Conversation context resets between sessions (no persistent memory)

## API Requirements

- Requires a valid `ANTHROPIC_API_KEY`
- Uses Claude 3.5 Sonnet (model: `claude-opus-5-5`)
- Requires internet connection for Anthropic API calls
