# HR Policy Agent

A Python agent that answers employees' questions about company HR policies using Claude AI.

## Features

- **Interactive Chat**: Engage in multi-turn conversations about HR policies
- **Single Question Mode**: Ask a question directly from the command line
- **Policy Context**: All policies are loaded into the Claude context for accurate answers
- **Conversation History**: Maintains conversation history for contextual follow-ups

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

### Interactive Chat Mode

Run the agent without arguments to start an interactive chat:

```bash
python3 agent.py
```

Then ask questions naturally:
```
You: How much annual leave do I get?
Assistant: [Answer about annual leave policy...]

You: What about sick leave?
Assistant: [Answer about sick leave...]

You: exit
```

### Single Question Mode

Ask a single question from the command line:

```bash
python3 agent.py "How much annual leave do I get as a full-time employee?"
```

The agent will answer and exit.

## Components

### `agent.py`
The main agent script with the following functions:

- `load_policies()`: Loads all markdown policy files from the `policies/` directory
- `create_system_prompt()`: Creates the system prompt with policy context
- `chat_with_agent()`: Runs an interactive chat session
- `answer_question()`: Answers a single question
- `main`: Entry point that handles both interactive and command-line modes

### `llm.py`
Wrapper around the Anthropic Messages API. Includes:

- `complete()`: Sends messages to Claude with optional tools
- `text_of()`: Extracts text from the response

### `test_agent.py`
Test suite covering:

- Policy loading
- System prompt creation
- Question answering (mocked and real)

## HR Policies

The agent references the following policies:

1. **Leave Policy** (`policies/leave.md`)
   - Annual leave (20 days for full-time)
   - Sick leave (10 days)
   - Parental leave (26 weeks)

2. **Remote Work Policy** (`policies/remote-work.md`)
   - Up to 3 days per week remote work
   - Overseas work requirements
   - Home office allowance

3. **Equipment Policy** (`policies/equipment.md`)
   - Laptop refresh cycle
   - Device loss reporting
   - Personal device access

4. **Travel Policy** (`policies/travel.md`)

5. **Expenses Policy** (`policies/expenses.md`)

## Running Tests

```bash
python3 test_agent.py
```

Tests include:
- Policy loading verification
- System prompt creation
- Mock-based question answering
- Real LLM integration (when API key is available)

## Model Configuration

By default, the agent uses `claude-sonnet-5-5`. To use a different model:

```bash
export MODEL=claude-opus-5-5
python3 agent.py
```

## Example Interactions

```
You: What if I need to work from overseas for a month?
Assistant: According to the remote work policy, working from overseas for more than 2 weeks 
requires HR and tax approval in advance. Since you're planning to work from overseas for a 
month (which exceeds 2 weeks), you'll need to:
1. Get approval from HR
2. Get tax approval
These approvals should be obtained before you travel.

You: Can I use my personal laptop for work email?
Assistant: According to the equipment policy, personal devices may access email only through 
the Intune app. This ensures your personal device remains secure and company data is protected.

You: How many days of sick leave do I get each year?
Assistant: You get 10 days of paid sick leave per year. However, if you need to take 3 or more 
consecutive days of sick leave, you'll need to provide a medical certificate.
```

## Design Considerations

- **Conversation Context**: The agent maintains conversation history to provide contextual responses
- **Policy Accuracy**: All answers are grounded in the actual policy documentation
- **User Experience**: Clear error handling and friendly prompts
- **Extensibility**: Easy to add new policies or modify the system prompt

## Future Enhancements

- Add tool use for structured data (policy updates, employee lookups)
- Support for policy version tracking
- Feedback mechanism for answer quality
- Multi-language support
- Integration with HR management systems
