# HR Policy Agent - Development Guide

This guide covers how to develop, extend, and deploy the HR Policy Agent.

## Project Structure

```
hr-policy-agent/
├── policies/                    # HR policy markdown files
│   ├── equipment.md
│   ├── expenses.md
│   ├── leave.md
│   ├── remote-work.md
│   └── travel.md
├── hr_agent.py                  # Simple interactive agent
├── hr_agent_advanced.py         # Advanced agent with features
├── test_agent.py                # Test suite with sample questions
├── example_usage.py             # Programmatic usage examples
├── requirements.txt             # Python dependencies
├── README.md                    # User guide
├── DEVELOPMENT.md               # This file
└── .chat_history.json          # (Generated) Conversation history
```

## Core Components

### `hr_agent.py` - Simple Interactive Agent

The simplest entry point. Features:
- Interactive multi-turn conversation
- Automatic policy loading from `policies/` directory
- Conversation history support
- Basic error handling

**Use when:** You want a quick, lightweight agent for testing.

### `hr_agent_advanced.py` - Advanced Agent

An enhanced version with:
- Command interface (`/help`, `/clear`, `/save`, `/load`)
- Persistent conversation history saved to JSON
- Policy management commands
- Better error handling and user feedback

**Use when:** You need a production-ready interactive agent.

### `test_agent.py` - Test Suite

Demonstrates the agent with predefined questions:
- Tests basic functionality
- Validates responses for correctness
- Suitable for CI/CD pipelines

**Use when:** Validating that the agent works correctly.

### `example_usage.py` - Programmatic API

Shows how to use the agent as a library:
- Single question queries
- Multi-turn conversations
- Complex scenarios
- Edge case handling

**Use when:** Integrating the agent into other applications.

## How It Works

### System Prompt Strategy

All policies are embedded in the system prompt (RAG without external DB):

1. Policies are loaded from markdown files
2. Formatted into a structured system prompt
3. Sent with each API call to Claude
4. Claude answers based on the provided context

**Advantages:**
- No external vector database needed
- Fast for small policy sets
- Easy to version control policies with git

**Limitations:**
- Token cost increases with policy size
- Not ideal for very large policy sets (1000+)

### Conversation Flow

```
User Question
    ↓
Add to conversation history
    ↓
Call Claude API with:
  - System prompt (with all policies)
  - Conversation history
  - User question
    ↓
Claude generates response
    ↓
Add response to history
    ↓
Save history to file
    ↓
Display to user
```

## Adding New Policies

1. Create a new markdown file in `policies/`:
   ```bash
   echo "# New Policy\nPolicy content here..." > policies/new_policy.md
   ```

2. The agent automatically loads it on next run

3. No code changes needed!

## Customizing the Agent

### Change the Model

Edit the `model` parameter in API calls:

```python
response = client.messages.create(
    model="claude-opus-5-5",  # Change this
    max_tokens=1024,
    system=system_prompt,
    messages=conversation_history
)
```

Available models:
- `claude-opus-5-5` - Most capable (default)
- `claude-sonnet-5-5` - Faster, good for many queries
- `claude-haiku-5-5` - Fastest, cost-effective

### Modify the System Prompt

Edit the `build_system_prompt()` function to change:
- Response style and tone
- Answer structure
- Additional guidelines
- Example responses

Example modification:
```python
def build_system_prompt(policies):
    return f"""...[policies]...
    
Additional instruction: Always format policy numbers in bold.
Provide specific section references when citing policies."""
```

### Add Command-Specific Behavior

In `hr_agent_advanced.py`, add new commands:

```python
elif user_input == "/my_command":
    # Your custom logic here
    print("Command executed!")
```

## Testing

### Manual Testing

```bash
python3 hr_agent.py
```

Then ask questions and verify responses.

### Automated Testing

```bash
python3 test_agent.py
```

Runs through predefined questions and outputs responses.

### Programmatic Testing

```python
from example_usage import query_agent

response, history = query_agent("Your question?", [])
assert "expected content" in response
```

## Integration Examples

### Flask Web API

```python
from flask import Flask, request, jsonify
from example_usage import query_agent

app = Flask(__name__)
history = []

@app.route('/ask', methods=['POST'])
def ask_policy_question():
    question = request.json['question']
    response, history = query_agent(question, history)
    return jsonify({'answer': response})

if __name__ == '__main__':
    app.run()
```

### Discord Bot

```python
import discord
from example_usage import query_agent

client = discord.Client()
conversation_histories = {}

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    user_id = message.author.id
    if user_id not in conversation_histories:
        conversation_histories[user_id] = []
    
    response, conversation_histories[user_id] = query_agent(
        message.content,
        conversation_histories[user_id]
    )
    
    await message.reply(response)
```

### Slack Bot

```python
from slack_bolt import App
from example_usage import query_agent

app = App(token=SLACK_BOT_TOKEN)
user_histories = {}

@app.message(".*")
def handle_message(message, say):
    user_id = message['user']
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    response, user_histories[user_id] = query_agent(
        message['text'],
        user_histories[user_id]
    )
    
    say(response)
```

## Performance Considerations

### Token Usage

- Each policy adds ~50-200 tokens to the system prompt
- Conversation history adds 1-2 tokens per word
- Monitor costs with: `len(system_prompt.split()) * 4 / 3` (rough estimate)

### Latency

- ~1-2 seconds per request (typical)
- First request might be slower due to model warm-up
- Consider caching for common questions

### Scaling

For production use:
1. **Cache policy embeddings** for faster retrieval
2. **Batch questions** if processing many at once
3. **Use streaming** for long responses
4. **Add rate limiting** to prevent abuse

## Debugging

### Enable Debug Output

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect System Prompt

```python
from hr_agent import build_system_prompt, load_policies
policies = load_policies()
print(build_system_prompt(policies))
```

### Check Conversation History

```python
import json
with open('.chat_history.json') as f:
    history = json.load(f)
    for msg in history:
        print(f"{msg['role']}: {msg['content'][:100]}...")
```

## Common Issues

### Agent gives wrong answer
- Check if the policy is correctly formatted in the markdown
- Verify the policy is in the `policies/` directory
- Try rephrasing the question

### API key not found
- Set `export ANTHROPIC_API_KEY="your-key-here"`
- Check `.env` files and shell configuration

### Memory/history not persisting
- Ensure write permissions for `.chat_history.json`
- Check file isn't being deleted elsewhere
- Use `hr_agent_advanced.py` for better history management

## Future Enhancements

- [ ] Semantic search with embeddings
- [ ] Policy versioning and change tracking
- [ ] Employee-specific personalization
- [ ] Integration with HRIS systems
- [ ] Multi-language support
- [ ] Audit logging for compliance
- [ ] Fine-tuned model for domain-specific accuracy
- [ ] Web UI with FastAPI/React
- [ ] Mobile app
- [ ] Slack/Teams integration

## Contributing

To contribute improvements:

1. Test your changes with `test_agent.py`
2. Update README if adding features
3. Follow the existing code style
4. Add docstrings to new functions
5. Consider performance and token usage

## Resources

- [Anthropic API Documentation](https://docs.anthropic.com)
- [Claude Models](https://docs.anthropic.com/claude/reference/models-overview)
- [System Prompts Best Practices](https://docs.anthropic.com/claude/guides/system-prompts)
