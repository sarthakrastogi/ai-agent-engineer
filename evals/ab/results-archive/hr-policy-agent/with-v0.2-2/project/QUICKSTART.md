# HR Policy Agent - Quick Start Guide

Get the HR Policy Agent running in 5 minutes.

## Prerequisites

- Python 3.8+
- An Anthropic API key (get one at https://console.anthropic.com)

## Installation & Setup

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set Your API Key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Step 3: Run the Agent

Choose one of three ways to run:

#### Option A: Interactive Chat (Recommended for users)

```bash
python3 hr_agent.py
```

Start asking questions:
```
You: How many days of annual leave do I get?
Assistant: Based on the Leave policy, full-time employees accrue 20 days...

You: What about part-time employees?
Assistant: For part-time staff, annual leave is pro-rated...
```

Type `exit` or `quit` to stop.

#### Option B: Advanced Interactive Agent (Recommended for frequent use)

```bash
python3 hr_agent_advanced.py
```

Additional features:
- `/help` - Show available commands
- `/policies` - List all HR policies
- `/clear` - Clear conversation history
- `/save` - Save current chat
- `/load` - Restore previous chat

#### Option C: Run Test Suite

```bash
python3 test_agent.py
```

Automatically tests 6 common questions and shows responses.

## Common Questions

### "How do I ask about a specific policy?"

Just ask naturally:
- "What's the remote work policy?"
- "How much parental leave can I take?"
- "What's the equipment refresh cycle?"

### "Can I use this programmatically?"

Yes! Check `example_usage.py`:

```python
from example_usage import query_agent

response, history = query_agent("Your question?", [])
print(response)
```

### "How do I add a new HR policy?"

1. Create a new file in `policies/` directory:
   ```bash
   touch policies/my_new_policy.md
   ```

2. Add policy content in markdown format

3. Restart the agent - it automatically loads new policies!

### "Can I customize the agent's behavior?"

Yes! Edit the `build_system_prompt()` function in any of the agent files to:
- Change response style
- Add guidelines
- Modify instructions

### "How do I see my chat history?"

The agent saves history to `.chat_history.json`. View it with:

```bash
cat .chat_history.json | python -m json.tool
```

Or use the advanced agent's `/save` command.

## Troubleshooting

### "ModuleNotFoundError: No module named 'anthropic'"

Make sure you ran:
```bash
pip install -r requirements.txt
```

### "Error: API key not found"

Set your API key:
```bash
export ANTHROPIC_API_KEY="your-actual-key"
```

Verify it's set:
```bash
echo $ANTHROPIC_API_KEY
```

### "Agent says 'I don't know'"

This usually means:
1. The policy isn't in the `policies/` directory
2. The answer requires information outside the policies
3. Try rephrasing your question

### "No response after waiting"

The API might be slow. Try again or check your internet connection.

## Next Steps

### Learn More
- Read [README.md](README.md) for detailed features
- Check [DEVELOPMENT.md](DEVELOPMENT.md) for advanced usage
- Review [example_usage.py](example_usage.py) for code examples

### Deploy
- Web API: Use FastAPI or Flask wrapper
- Chat platform: Integrate with Slack, Discord, Teams
- Enterprise: Use with HRIS systems

### Customize
- Add company-specific policies to `policies/` directory
- Modify system prompt for tone/style
- Switch models (Sonnet for speed, Opus for quality)

## Tips & Tricks

**🎯 Get better answers:**
- Be specific: "Can I work from overseas for 3 weeks?" vs "Remote work policy?"
- Ask follow-ups: The agent remembers your conversation
- Provide context: "I'm part-time, so..." helps the agent tailor responses

**⚡ Use efficiently:**
- Questions answered in ~1-2 seconds
- Multiple questions in one session are faster
- The agent learns from context as you chat

**💾 Save conversations:**
```bash
python3 hr_agent_advanced.py
# ... ask questions ...
# /save (to save)
# /exit
```

## Example Conversation

```
$ python3 hr_agent.py

HR Policy Agent
============================================================

Welcome! I'm here to help you understand company HR policies.
Type 'exit' or 'quit' to end the conversation.

You: I'm planning a trip to Australia for 2 weeks. Do I need approval?
Assistant: Based on the Travel policy, international travel requires director approval. 
You'll need to:
1. Get director approval before booking
2. Book through TravelDesk
3. For flights over 6 hours, you can use premium economy

You: What about my meals during the trip?
Assistant: According to the Expenses policy, meals while travelling are covered up to 
NZD 80 per day with an itemised receipt. Submit your claims in the Expenso app 
within 60 days of purchase.

You: Can I work from Australia for a week after my meetings?
Assistant: Based on the Remote work policy, working from overseas for more than 
2 weeks requires HR and tax approval in advance. Since your initial trip is 2 weeks, 
extending to 3 weeks would require HR and tax approval. I recommend contacting HR 
to discuss your specific situation.

You: exit
Thank you for using the HR Policy Agent. Goodbye!
```

## Support

For issues or questions:
1. Check [DEVELOPMENT.md](DEVELOPMENT.md) for technical details
2. Review [README.md](README.md) for feature documentation
3. Check your API key and internet connection
4. Contact your HR department for policy interpretation questions

---

**Ready to get started?** Run `python3 hr_agent.py` now!
