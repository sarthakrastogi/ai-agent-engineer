# HR Policy Agent

A Python agent that helps employees find answers to their HR policy questions using Claude AI.

## Overview

This project provides two ways to interact with the HR policy agent:

1. **Interactive Chat** (`hr_agent.py`) - A conversational interface where employees can ask questions in real-time
2. **Test Suite** (`test_agent.py`) - Automated tests demonstrating the agent answering common HR questions

## Features

- 📚 Supports multiple HR policies: Leave, Remote Work, Travel, Equipment, and Expenses
- 💬 Multi-turn conversation support - ask follow-up questions in context
- 🎯 Policy-aware responses with citations
- ✅ Graceful handling of out-of-scope questions
- 🛡️ Clear acknowledgment of policy limitations

## Setup

### Prerequisites

- Python 3.8 or higher
- An Anthropic API key

### Installation

1. Clone or navigate to this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

## Usage

### Interactive Chat

Run the interactive agent:

```bash
python3 hr_agent.py
```

Example conversation:
```
You: How many days of annual leave do I get?
Assistant: Based on the Leave policy, full-time employees accrue 20 days of annual leave per year...

You: What if I'm part-time?
Assistant: For part-time staff, annual leave is pro-rated...
```

### Run Tests

Test the agent with predefined questions:

```bash
python3 test_agent.py
```

This will run through a series of common HR questions and display the agent's responses.

## HR Policies Covered

The agent has access to the following policies in the `policies/` directory:

- **leave.md** - Annual leave, sick leave, and parental leave policies
- **remote-work.md** - Remote work arrangements and home office allowances
- **travel.md** - Travel booking and approval requirements
- **equipment.md** - Laptop refresh cycles and device security
- **expenses.md** - Expense claim procedures, limits, and approvals

## Architecture

The agent uses:

- **Model**: Claude 3.5 Opus for accurate, context-aware responses
- **Approach**: Retrieval-Augmented Generation (RAG) - all policies are included in the system prompt
- **Interface**: Python CLI with multi-turn conversation history

## Example Questions

The agent can answer questions like:

- "How many days of annual leave do I get?"
- "Can I work from home? What are the requirements?"
- "What's the process for international travel?"
- "How much can I claim for business meals?"
- "What should I do if my equipment is lost or stolen?"
- "How long is parental leave?"

## Limitations

- The agent only answers questions based on the policies provided
- For complex or policy-ambiguous situations, it recommends contacting HR directly
- It does not have access to individual employee records or personalized information

## Development

To extend the agent:

1. **Add new policies**: Add markdown files to the `policies/` directory
2. **Customize responses**: Edit the `build_system_prompt()` function in either Python file
3. **Change the model**: Modify the `model` parameter in the API calls

## Future Enhancements

- Vector database for semantic search over policies
- Web interface with FastAPI
- Integration with HR systems (e.g., pulling employee tenure for parental leave eligibility)
- Multi-language support
- Audit logging for compliance
- Feedback mechanism to improve responses
