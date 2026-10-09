# HR Policy Agent - Configuration Guide

Configure the HR Policy Agent for your environment and use case.

## Environment Variables

### Required

**`ANTHROPIC_API_KEY`** - Your Anthropic API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Get your key from https://console.anthropic.com/account/keys

## Model Selection

The agent uses `claude-opus-5-5` by default. Choose based on your needs:

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `claude-opus-5-5` | Slow | High | Accuracy, complex reasoning |
| `claude-sonnet-5-5` | Medium | Medium | Balanced performance |
| `claude-haiku-5-5` | Fast | Low | High volume, simple queries |

### Change the Model

Edit the `model` parameter in the agent files:

**hr_agent.py (line ~85):**
```python
response = client.messages.create(
    model="claude-sonnet-5-5",  # Change here
    max_tokens=1024,
    system=system_prompt,
    messages=conversation_history
)
```

## Customizing System Behavior

### Response Length

Adjust `max_tokens` parameter (default: 1024):

```python
response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=512,  # Shorter responses
    # or
    max_tokens=2048,  # Longer responses
    system=system_prompt,
    messages=conversation_history
)
```

### Response Style

Modify `build_system_prompt()` to change tone:

**Professional & Formal:**
```python
Additional instructions:
- Use formal language
- Provide precise policy references
- Format numbers with dollar signs and decimals
```

**Conversational & Friendly:**
```python
Additional instructions:
- Use a friendly, helpful tone
- Explain policies in simple terms
- Use emojis where appropriate
- Provide examples from employee perspectives
```

**Concise & Direct:**
```python
Additional instructions:
- Answer in 1-2 sentences when possible
- Include only essential information
- Use bullet points for clarity
```

## Policy Management

### Adding Policies

1. Create a markdown file in `policies/`:
   ```bash
   cat > policies/benefits.md << 'EOF'
   # Benefits Policy
   
   Company provides:
   - Health insurance
   - Dental coverage
   - Gym membership
   EOF
   ```

2. Restart the agent - new policies are automatically loaded

### Updating Policies

Edit the corresponding markdown file:
```bash
nano policies/leave.md
```

Changes take effect on next restart.

### Removing Policies

Delete the file:
```bash
rm policies/old_policy.md
```

## Advanced Configuration

### Custom System Instructions

Create a custom version with your instructions:

```python
def build_custom_system_prompt(policies):
    policies_text = "\n\n".join(...)
    
    return f"""You are an HR Policy Assistant.

TONE: Professional but approachable
LANGUAGE: Use "employees" instead of "team members"
EMPHASIS: Always highlight compliance requirements

Policies:
{policies_text}

RESPONSE FORMAT:
1. Direct answer to the question
2. Relevant policy section
3. Example or clarification
4. Next steps if applicable
"""
```

### Adding Context Variables

```python
def build_system_prompt_with_context(policies, company_name="Our Company"):
    # ... existing code ...
    return f"""... This is {company_name}'s HR Policy Assistant."""
```

### Conversation History Location

Change where chat history is saved:

**In hr_agent_advanced.py:**
```python
def __init__(self, history_file: str = "/custom/path/.chat_history.json"):
    self.history_file = Path(history_file)
    # ...
```

## Scaling Configuration

### Single User (Development)
- Default settings are fine
- Use `hr_agent.py` for quick testing

### Small Team (5-50 users)
- Use `hr_agent_advanced.py` with persistent history
- Consider `claude-sonnet-5-5` for cost efficiency
- Save history per user/department

### Enterprise (100+ users)
- Set up API with rate limiting
- Use vector database for policies
- Consider caching common questions
- Monitor token usage and costs

### Configuration Example for Enterprise

```python
import redis
from functools import lru_cache

# Cache common questions
cache = redis.Redis(host='localhost', port=6379)

@lru_cache(maxsize=1000)
def query_agent_cached(question):
    """Return cached response if available."""
    cached = cache.get(f"q:{question}")
    if cached:
        return cached.decode()
    
    response, _ = query_agent(question, [])
    cache.setex(f"q:{question}", 3600, response)
    return response
```

## Performance Tuning

### Reduce Latency

**Option 1: Use faster model**
```python
model="claude-haiku-5-5"  # Fastest
```

**Option 2: Reduce token count**
- Use shorter policy descriptions
- Remove examples from system prompt
- Reduce max_tokens to 512

**Option 3: Enable streaming**
```python
# For long responses, show first token immediately
response = client.messages.stream(...)
```

### Reduce Costs

**Option 1: Use cheaper model**
```python
model="claude-haiku-5-5"  # Cheapest
```

**Option 2: Compress policies**
- Remove redundant information
- Use abbreviations
- Consolidate similar policies

**Option 3: Cache responses**
- Store Q&A pairs
- Reuse for similar questions
- Reduce repeat API calls

## Testing Configuration

### Enable Debug Logging

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### Monitor API Usage

```python
from anthropic import Anthropic

client = Anthropic()
# Each response includes usage info
response = client.messages.create(...)
print(f"Tokens used: {response.usage.input_tokens + response.usage.output_tokens}")
```

### Test Different Models

```python
models = ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"]

for model in models:
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": "How many vacation days?"}]
    )
    print(f"{model}: {response.content[0].text[:100]}")
```

## Deployment Configuration

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

CMD ["python3", "hr_agent_advanced.py"]
```

### Environment File (.env)

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
AGENT_MODEL=claude-opus-5-5
AGENT_MAX_TOKENS=1024
HISTORY_FILE=/app/data/.chat_history.json
```

Load in Python:
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')
model = os.getenv('AGENT_MODEL', 'claude-opus-5-5')
```

## Monitoring & Metrics

### Track Common Questions

```python
import json
from collections import Counter

def log_question(question):
    with open('questions.log', 'a') as f:
        f.write(json.dumps({'q': question, 't': time.time()}) + '\n')

# Analyze
questions = Counter(line['q'] for line in ...)
print(questions.most_common(10))
```

### Track Success Rate

```python
def track_response(question, response, user_feedback):
    """Log response quality."""
    with open('quality.log', 'a') as f:
        f.write(json.dumps({
            'q': question,
            'helpful': user_feedback
        }) + '\n')
```

## Troubleshooting Configuration

### Agent responses are too long/short

Adjust `max_tokens`:
- Too long: Reduce to 512
- Too short: Increase to 2048

### Agent ignoring instructions

Ensure instructions are in `build_system_prompt()` before the policies section.

### API calls too slow

1. Switch to faster model
2. Reduce conversation history length
3. Implement caching

### High costs

1. Switch to `claude-haiku-5-5`
2. Compress policies
3. Cache responses
4. Limit conversation history length

---

For more help, see:
- [README.md](README.md) - Feature overview
- [DEVELOPMENT.md](DEVELOPMENT.md) - Technical details
- [QUICKSTART.md](QUICKSTART.md) - Getting started
