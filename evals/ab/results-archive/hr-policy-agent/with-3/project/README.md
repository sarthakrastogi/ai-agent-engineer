# HR Policy Agent

A small, practical agent that answers employee questions about company HR policies with citations to the actual policy documents.

## Features

- **Retrieval-augmented:** Finds the most relevant policies for each question
- **Cited answers:** Every answer cites which policy it comes from
- **Scope-aware:** Declines to answer non-HR-policy questions
- **Fast & cheap:** Single LLM call, ~200 tokens, <$0.01 per question
- **Maintainable:** Policies are plain markdown; add new ones to `policies/` and they're automatically picked up

## Quick start

### Install dependencies

```bash
pip install -r requirements.txt
```

### Interactive mode

```bash
python3 agent.py
```

Example questions:
- "How many days of annual leave do full-time employees get?"
- "Can I work from home?"
- "What's the meal allowance while travelling?"
- "When do I get a new laptop?"

### Programmatic API

```python
from agent import answer_question

question = "How much parental leave can I take?"
answer = answer_question(question)
print(answer)
```

## Architecture

```
Employee Question
      ↓
  Retrieve (keyword matching on policy text)
      ↓
 Build system prompt with relevant policies
      ↓
 Call Claude (single turn)
      ↓
   Answer with citations
```

**Why this design?**
- Single LLM call: No loops, simple and fast
- Keyword retrieval: Policy corpus is small (~2k tokens), keywords are reliable
- System-prompt context: Ensures consistent, cited answers
- No tools: Questions need only context, not side effects

See [DESIGN.md](DESIGN.md) for full architecture, alternatives considered, and limitations.

## Testing

```bash
# Run all tests
python3 -m pytest test_agent.py -v

# Run specific test class
python3 -m pytest test_agent.py::TestRetrieval -v

# Run with output (useful for debugging)
python3 -m pytest test_agent.py -v -s
```

Tests cover:
- Retrieval ranking (does keyword matching find the right policies?)
- Answer quality (are answers cited and factual?)
- Scope handling (does the agent decline out-of-scope questions?)
- End-to-end flows (do full Q&A cycles work?)

## Project structure

```
├── agent.py              # Main agent implementation
├── llm.py                # Anthropic API wrapper
├── test_agent.py         # Test suite
├── DESIGN.md             # Architecture & design decisions
├── policies/             # HR policy markdown files
│   ├── leave.md
│   ├── remote-work.md
│   ├── expenses.md
│   ├── equipment.md
│   └── travel.md
└── requirements.txt      # Python dependencies
```

## How to extend

### Add a new policy

1. Create a markdown file in `policies/`, e.g., `policies/training.md`
2. Start with a clear header: `# Training Policy`
3. Add sections with markdown headings (##, ###)
4. The agent will auto-load it on the next run

### Improve retrieval

Keyword matching works well for this corpus. If you find retrieval failures:

1. Add a test case to `test_agent.py` with the failing question
2. Check the `retrieve_relevant_policies()` function's scoring logic
3. Options:
   - Add keywords to policy headers (e.g., "Remote Work (WFH, work from home)")
   - Use synonym expansion in the retrieval function
   - Switch to embedding-based retrieval if corpus grows significantly

### Change the LLM

Edit the `MODEL` in `llm.py`:

```python
MODEL = os.environ.get("MODEL", "claude-opus-5-5")  # or claude-haiku-5-5
```

Or pass via environment variable:

```bash
MODEL=claude-opus-5-5 python3 agent.py
```

## Design decisions

See [DESIGN.md](DESIGN.md) for:
- Why keyword retrieval instead of embeddings
- Why single LLM call instead of multi-agent
- Trade-offs and known limitations
- Measurement plan for production

## License

Company internal use.
