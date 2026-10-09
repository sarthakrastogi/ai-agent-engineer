# HR Policy Agent

A Python-based conversational agent that answers employee questions about company HR policies using Claude AI.

## Features

- **Conversational Interface**: Interactive chat-style questions and answers
- **Policy Context**: Automatically loads all HR policies from the `policies/` directory
- **Accurate Responses**: Uses Claude to provide knowledgeable, policy-compliant answers
- **Multi-turn Conversations**: Maintains conversation history for context-aware responses
- **Friendly & Professional**: Trained to be helpful, clear, and professional

## Policies Covered

The agent answers questions about the following HR policies:
- **Leave**: Annual leave, sick leave, parental leave
- **Expenses**: Claims, limits, and approval requirements
- **Remote Work**: Remote work allowances and international work approvals
- **Travel**: Flight booking and travel approval requirements
- **Equipment**: Device refresh cycles and security policies

## Setup

### Prerequisites

- Python 3.8 or higher
- An Anthropic API key

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

## Usage

Run the agent:

```bash
python hr_agent.py
```

Once started, you can ask questions about HR policies:

```
Welcome to the HR Policy Agent!
Ask questions about company HR policies.
Type 'exit' or 'quit' to end the conversation.
============================================================

You: How many days of annual leave do I get?

Agent: According to the leave policy, full-time employees accrue 20 days of 
annual leave per year. If you're part-time, this is pro-rated based on your hours. 
You can carry over up to 5 unused days to the next year, but any additional unused 
days will lapse on 31 March.

You: What about sick leave?

Agent: You're entitled to 10 days of paid sick leave per year. If you need to take 
3 or more consecutive days off, you'll need to provide a medical certificate.

You: exit

Thank you for using the HR Policy Agent. Goodbye!
```

## How It Works

1. **Policy Loading**: The agent reads all markdown files from the `policies/` directory
2. **System Prompt**: Creates a comprehensive system prompt that includes all policies as context
3. **Conversation Management**: Maintains conversation history for multi-turn interactions
4. **Claude Integration**: Uses the Claude API to generate helpful, accurate responses based on policies

## Architecture

- `load_policies()`: Reads and combines all policy markdown files
- `create_system_prompt()`: Builds the system prompt with embedded policies
- `run_hr_agent()`: Main conversational loop that manages user interaction
- `main()`: Entry point for the script

## Adding New Policies

Simply add new markdown files to the `policies/` directory with the naming convention `policy-name.md`. 
The agent will automatically load and incorporate them on the next run.

## Error Handling

- If the `policies/` directory is not found, the agent will display an error message
- If there's an API communication error, it will be reported and the conversation will continue
- Individual policy file errors are logged as warnings but don't prevent the agent from starting

## Notes

- The agent maintains conversation history within a single session
- Each time you start the agent, it begins with a fresh conversation
- The agent respects the policy context and won't make up or speculate beyond the provided policies
