# HR Policy Agent

A Python agent that answers employees' questions about company HR policies using Claude AI.

## Overview

This project contains:
- **HR Policies** in `policies/` directory (leave, remote-work, equipment, expenses, travel)
- **LLM Wrapper** (`llm.py`) — thin wrapper over the Anthropic Messages API
- **Agent** (`agent.py`) — an agentic loop that uses Claude with tool use to answer policy questions
- **Tests** (`test_agent.py`) — basic validation of agent functionality
- **Demo** (`demo.py`) — example questions and answers

## Architecture

The agent uses Claude with a **lookup_policy** tool that lets it search for specific policies when needed:

1. User asks a question about HR policies
2. Agent uses the Claude Messages API with tool use enabled
3. Agent calls `lookup_policy` to retrieve relevant policy documents
4. Agent synthesizes the policy information into a helpful answer
5. Loop continues if more policies need to be consulted

## Setup

```bash
# Install dependencies
pip install anthropic

# Set API key
export ANTHROPIC_API_KEY=your-key-here
```

## Usage

### Interactive mode

```bash
python3 agent.py
```

Starts an interactive loop where you can ask questions about HR policies.

### Run the demo

```bash
python3 demo.py
```

Runs the agent on predefined example questions to see it in action.

### Run tests

```bash
python3 test_agent.py
```

Validates that policies load correctly and the agent's tools work.

## Example Questions

- "How many days of annual leave do I get?"
- "Can I work from home?"
- "What happens if I need to take sick leave?"
- "When do I get a new laptop?"
- "I want to work remotely from overseas for a month, is that allowed?"

## Files

- `agent.py` — Main agent implementation
- `llm.py` — Anthropic API wrapper
- `demo.py` — Demo script with example questions
- `test_agent.py` — Tests for agent components
- `policies/` — HR policy markdown files
  - `leave.md` — Annual, sick, and parental leave
  - `remote-work.md` — Remote work guidelines
  - `equipment.md` — Device and laptop policy
  - `expenses.md` — Expense reimbursement policy
  - `travel.md` — Business travel policy
