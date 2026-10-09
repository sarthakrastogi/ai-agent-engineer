# HR Policy Agent - Quick Start Guide

## Setup (2 minutes)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API key:**
   ```bash
   export ANTHROPIC_API_KEY=your-key-here
   ```

## Run the Agent

### Interactive Chat Mode
```bash
python3 hr_agent.py
```

Then ask questions like:
- "How much annual leave do I get?"
- "Can I work from home?"
- "What's the travel policy?"
- Type `exit` to quit

### Test with Sample Questions
```bash
python3 test_agent.py
```

### Use as a Library
```python
from example_usage import HRPolicyAgent

agent = HRPolicyAgent()
answer = agent.ask("How many days of sick leave do I get?")
print(answer)
```

## Project Structure

```
hr-policy-agent/
├── hr_agent.py           # Main interactive agent
├── test_agent.py         # Test script with sample questions
├── example_usage.py      # Library usage example
├── requirements.txt      # Python dependencies
├── policies/             # HR policy documents
│   ├── leave.md
│   ├── remote-work.md
│   ├── travel.md
│   ├── equipment.md
│   └── expenses.md
└── README.md            # Full documentation
```

## Features

✅ **Policy-backed answers** - All responses grounded in actual policies
✅ **Multi-turn conversations** - Context maintained across questions  
✅ **Citations** - Relevant policy sections referenced in answers
✅ **Interactive & Programmatic** - Use via CLI or as a Python library

## Common Questions

**Q: How does it work?**
A: The agent loads all HR policy markdown files, includes them in the system prompt sent to Claude, and uses Claude to answer questions based on those policies.

**Q: Can employees use this?**
A: Yes! Just run `python3 hr_agent.py` and they can ask questions interactively.

**Q: Can I integrate it into our app?**
A: Yes! Use the `HRPolicyAgent` class from `example_usage.py` as a library in your application.

**Q: What if the policy doesn't cover a question?**
A: The agent will clearly state it doesn't have that information and suggest contacting HR.

## Adding New Policies

1. Create a new markdown file in `policies/` (e.g., `training.md`)
2. Write the policy content in markdown format
3. Restart the agent - it will automatically load the new policy

## Support

For issues or questions about the agent:
- Check the full README.md for detailed documentation
- Review the policy files in the `policies/` directory
- Run `test_agent.py` to verify everything is working
