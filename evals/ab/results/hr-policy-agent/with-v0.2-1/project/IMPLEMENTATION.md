# HR Policy Agent Implementation

## Summary

Built a Python agent that answers employees' questions about company HR policies using Claude AI with tool use.

## Key Components

### 1. **agent.py** — Main Agent Implementation

The core agent implementation with:

- **`load_policies()`** — Loads all HR policy markdown files from `policies/`
- **`build_policy_lookup_tool()`** — Creates the Claude tool definition for policy lookup
- **`lookup_policy()`** — Executes policy lookups and returns content
- **`run_agent_loop()`** — Main agentic loop that:
  1. Takes a user question
  2. Calls Claude with the question and the `lookup_policy` tool
  3. Handles tool calls to fetch relevant policies
  4. Continues until Claude produces a final text response
  5. Returns the synthesized answer

### 2. **llm.py** — API Wrapper

Existing thin wrapper over the Anthropic API with:
- `complete()` — Makes API calls with system prompts, messages, tools, and token limits
- `text_of()` — Extracts text responses from Claude's content blocks

### 3. **Test Suite** — test_agent.py

Tests covering:
- ✓ Policy loading from filesystem
- ✓ Tool schema generation
- ✓ Policy lookup functionality
- ✓ Error handling for missing policies

All tests pass.

### 4. **Demo Script** — demo.py

Runs the agent on 5 example questions to showcase functionality:
1. Annual leave entitlement
2. Remote work availability
3. Sick leave procedures
4. Laptop refresh schedule
5. Overseas remote work policy

### 5. **Documentation** — README.md + IMPLEMENTATION.md

Complete setup and usage instructions.

## How It Works

```
User Question
    ↓
Claude Agent (with tools)
    ↓
Tool: lookup_policy("leave", "remote-work", etc.)
    ↓
Policy Content Retrieved
    ↓
Claude Synthesizes Answer
    ↓
Final Response to User
```

## Design Decisions

1. **Tool-based approach** — Uses Claude's tool use feature rather than RAG, keeping policies in markdown and letting Claude decide which ones to consult
2. **Agentic loop** — Allows multi-turn policy lookups for complex questions
3. **Structured schema** — Policy names are an enum in the tool schema so Claude can only request policies that exist
4. **Simple and maintainable** — Easy to add new policies (just drop a `.md` file in `policies/`)

## Usage Examples

```python
# Interactive mode
python3 agent.py

# Run demo
python3 demo.py

# Run tests
python3 test_agent.py
```

## Policies Available

The agent has access to 5 HR policy documents:
- **leave.md** — Annual (20 days), sick (10 days), parental (26 weeks) leave
- **remote-work.md** — Up to 3 days/week remote, overseas work requirements, home office allowance
- **equipment.md** — Laptop refresh every 3 years, device reporting, personal device access
- **expenses.md** — Expense reimbursement policy
- **travel.md** — Business travel guidelines

## Future Enhancements

- Add conversation memory for multi-turn discussions
- Implement policy search/keyword matching
- Add role-based policy filtering (e.g., manager-only policies)
- Create REST API endpoint for integration with HR systems
- Add policy versioning and change tracking
