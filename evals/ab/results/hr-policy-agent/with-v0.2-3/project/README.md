# HR Policy Agent

A Python agent that answers employee questions about company HR policies using Claude AI.

## Overview

The HR Policy Agent loads company HR policies from the `policies/` directory and uses Claude to provide accurate, policy-backed answers to employee inquiries. It maintains conversation context, so employees can ask follow-up questions naturally.

## Features

- **Policy-backed answers**: All responses are grounded in the actual policy documents
- **Multi-turn conversations**: Maintains context across multiple questions
- **Clear citations**: References the relevant policy sections in answers
- **Interactive CLI**: Simple command-line interface for easy use

## Policies Included

- **Leave**: Annual leave, sick leave, and parental leave entitlements
- **Remote Work**: Guidelines for remote work arrangements and home office support
- **Travel**: Business travel booking and approval requirements
- **Equipment**: Device provisioning and management policies
- **Expenses**: Expense claims, limits, and approval thresholds

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY=your-api-key-here
   ```

## Usage

### Interactive Mode

Run the agent in interactive mode to have a conversation with the HR Policy Assistant:

```bash
python3 hr_agent.py
```

You can then type questions and the agent will answer based on the HR policies:

```
HR Policy Agent Ready!
Ask any questions about HR policies. Type 'exit' or 'quit' to stop.

You: How much annual leave do I get?
Agent: Based on the Leave policy, full-time employees accrue 20 days of annual leave per year...

You: Can I carry over unused days?
Agent: Yes, according to the policy, up to 5 unused days can be carried over to the next year...
```

### Testing

Run the test script to see the agent in action with predefined questions:

```bash
python3 test_agent.py
```

This will run through a series of common HR questions and display the agent's responses.

## How It Works

1. **Load Policies**: The agent reads all markdown files from the `policies/` directory
2. **Build Context**: Creates a system prompt that includes all policies as reference material
3. **Process Questions**: Takes user questions and passes them to Claude along with the policy context
4. **Maintain History**: Keeps track of the conversation to allow follow-up questions
5. **Provide Answers**: Returns policy-grounded answers with relevant citations

## Architecture

- `hr_agent.py`: Main interactive agent application
- `test_agent.py`: Non-interactive test script with sample questions
- `policies/`: Directory containing all HR policy markdown files
- `requirements.txt`: Python dependencies

## Example Interactions

**Q: Can I work from overseas?**
A: Based on the Remote Work policy, you may work remotely up to 3 days per week with your manager's agreement. Working from overseas for more than 2 weeks requires HR and tax approval in advance.

**Q: What happens if I lose my laptop?**
A: According to the Equipment policy, lost or stolen devices must be reported to IT within 24 hours.

**Q: How long is parental leave?**
A: The Leave policy states that primary carers receive 26 weeks of paid parental leave after 6 months of service.
