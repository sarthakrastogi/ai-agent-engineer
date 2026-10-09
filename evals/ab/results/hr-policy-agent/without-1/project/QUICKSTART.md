# Quick Start Guide

## Installation

1. Install Python 3.8 or later
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   ```

## Running the Agent

### Option 1: Interactive Chat

Start a conversation with the HR policy assistant:

```bash
python3 agent.py
```

Example session:
```
HR Policy Assistant
==================================================
Ask me anything about company HR policies.
Type 'exit' or 'quit' to end the conversation.

You: How much annual leave do I get?
Assistant: According to the leave policy, full-time employees accrue 20 days of annual leave 
per year, pro-rated for part-time staff. Up to 5 unused days can be carried over to the next 
year; the rest lapses on March 31st.

You: Can I carry over all 20 days?
Assistant: No, you can only carry over up to 5 unused days to the next year. Any remaining 
unused days will lapse on March 31st. This encourages regular leave usage.

You: exit
Thank you for using the HR Policy Assistant. Goodbye!
```

### Option 2: Single Question

Ask a single question directly:

```bash
python3 agent.py "What is the home office allowance for remote work?"
```

Output:
```
According to the remote work policy, a home office allowance of NZD 400 is available once 
every 3 years. This can be used towards setting up or improving your home office setup.
```

### Option 3: With Tool Support (Advanced)

Run the agent with access to tools (requires implementation of tool handlers):

```bash
python3 agent_with_tools.py
```

This version can call tools to:
- Check employee leave balances
- Look up policy versions and effective dates
- Integrate with HR management systems

## Testing

Run the test suite:

```bash
python3 test_agent.py
```

Expected output:
```
✓ test_load_policies passed
✓ test_create_system_prompt passed
✓ test_answer_question passed
⊘ test_answer_question_with_real_llm skipped (no API key)

All tests passed!
```

## Configuration

### Change the Model

Use a different Claude model:

```bash
export MODEL=claude-opus-5-5
python3 agent.py
```

Available models:
- `claude-opus-5-5` (most capable)
- `claude-sonnet-5-5` (default, balanced)
- `claude-haiku-5-5` (fastest, lower cost)

### Modify System Prompt

Edit the `create_system_prompt()` function in `agent.py` to customize:
- The agent's behavior
- Response style
- Additional instructions

### Add New Policies

Simply add markdown files to the `policies/` directory. The agent will automatically load them:

```bash
echo "# New Policy
Some policy content" > policies/new-policy.md
```

## Common Questions

**Q: How are policies loaded?**
A: All markdown files in the `policies/` directory are loaded at startup and included in the Claude system prompt. This ensures the agent always has the current policies.

**Q: Does the agent learn?**
A: No, the agent doesn't persist learning. Each session starts fresh. However, conversation history is maintained within a session for contextual responses.

**Q: Can I use this in production?**
A: Yes! The agent is designed for real-world use. For production:
- Add error handling for API failures
- Implement rate limiting
- Log conversations for compliance
- Add authentication if needed
- Monitor API costs

**Q: How much does it cost?**
A: Pricing depends on the model and usage:
- Sonnet 5.5: $3 per 1M input tokens, $15 per 1M output tokens
- See https://www.anthropic.com/pricing for current rates

## Troubleshooting

**Error: No module named 'anthropic'**
```bash
pip install anthropic
```

**Error: API key not found**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**Agent gives generic responses**
- Ensure all policy files are in `policies/`
- Check that the Anthropic API key is valid
- Try a different model (see Configuration section)

## Next Steps

- Read the full documentation in `AGENT_README.md`
- Explore the code in `agent.py`
- Check out the tool-enabled version in `agent_with_tools.py`
- Run tests to verify the setup
