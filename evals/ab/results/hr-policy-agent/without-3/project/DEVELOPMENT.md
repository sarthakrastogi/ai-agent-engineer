# HR Policy Agent - Development Guide

## 🏗️ Architecture Overview

The HR Policy Agent is built with two tiers:

```
┌─────────────────────────────────────────┐
│         Employee Question               │
└────────────┬────────────────────────────┘
             │
      ┌──────▼──────┐
      │   Choose:   │
      │  - Demo     │
      │  - Full     │
      └──────┬──────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼──────┐     ┌────▼──────────┐
│  Demo    │     │  Full Agent   │
│ (Instant)│     │ (Claude API)  │
└───┬──────┘     └────┬──────────┘
    │                 │
    │  Keyword        │ Tool Use
    │  Matching       │ & Search
    │                 │
    └────────┬────────┘
             │
     ┌───────▼────────┐
     │ Relevant       │
     │ Policies       │
     └───────┬────────┘
             │
     ┌───────▼────────┐
     │ Formatted      │
     │ Response       │
     └───────────────┘
```

---

## 📂 File Organization

### Core Implementation
- **`hr_agent_demo.py`** (220 lines)
  - No dependencies
  - Keyword-based search
  - Instant responses
  - Test backend

- **`hr_agent.py`** (170 lines)
  - Requires anthropic SDK
  - Claude API integration
  - Tool use with search_policies
  - Multi-turn capable

### Testing & Utilities
- **`test_agent.py`** (95 lines)
  - Policy loading tests
  - Search accuracy tests
  - Query verification tests
  - Run with: `python3 test_agent.py`

- **`llm.py`** (21 lines)
  - API wrapper
  - Provided helper functions
  - Used by other tools

### Configuration
- **`requirements.txt`**
  - anthropic SDK
  - pytest (optional)

### Documentation
- **`README.md`** - Full guide
- **`QUICKSTART.md`** - Quick start
- **`SOLUTION.md`** - Architecture
- **`DEVELOPMENT.md`** - This file

### Data
- **`policies/`** folder
  - 5 markdown policy files
  - Auto-discovered by agent

---

## 🔍 How Search Works

### Demo Agent Search Algorithm

```python
# Step 1: Score each policy
for policy_name, content in policies.items():
    score = 0
    
    # Direct name match (weight 10)
    if query in policy_name:
        score += 10
    
    # Content match (weight 5)
    if query in content:
        score += 5
    
    # Keyword mapping match (weight 3)
    if policy_matches_keywords(policy_name, query):
        score += 3

# Step 2: Sort by score descending
results.sort(key=score, reverse=True)

# Step 3: Return top matches
return results
```

### Keyword Mapping

```python
keyword_mapping = {
    "leave": ["leave", "vacation", "sick", "parental"],
    "expenses": ["expense", "claim", "meal", "receipt"],
    "remote-work": ["remote", "home office", "overseas"],
    "travel": ["travel", "flight", "booking"],
    "equipment": ["equipment", "laptop", "device"],
}
```

---

## 🤖 Full Agent Tool Use

### Tool Definition
```python
tools = [
    {
        "name": "search_policies",
        "description": "Search HR policy information",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
    }
]
```

### Claude's Tool Loop
```
1. Claude receives question
2. Claude calls search_policies tool with query
3. Tool returns matching policies
4. Claude generates natural language response
5. Response returned to employee
```

---

## 🧪 Testing Strategy

### Test Categories

**1. Data Integrity Tests**
- Verify all policies load
- Check policy file format
- Validate content exists

**2. Search Accuracy Tests**
- Test each policy category
- Verify ranking order
- Check keyword matching

**3. Integration Tests**
- End-to-end question→answer
- Multiple policy matches
- No-match scenarios

**4. Regression Tests**
- Specific known queries
- Expected answer content
- Policy-specific details

### Running Tests
```bash
# Run full suite
python3 test_agent.py

# Run specific test
python3 -m pytest test_agent.py::test_search_leave -v

# Run with coverage
python3 -m pytest test_agent.py --cov
```

---

## 🎨 Customization Guide

### Adding New Policies

1. **Create policy file**
   ```bash
   touch policies/benefits.md
   ```

2. **Write policy content**
   ```markdown
   # Benefits Policy
   ## Health Insurance
   All employees receive coverage...
   
   ## Retirement Plans
   Matching contributions...
   ```

3. **Add keyword mapping** (optional, in `hr_agent_demo.py`)
   ```python
   keyword_mapping["benefits"] = ["benefit", "insurance", "retirement"]
   ```

4. **Test it works**
   ```bash
   python3 hr_agent_demo.py "Do you offer health insurance?"
   ```

### Improving Search

1. **Fine-tune keywords** for your organization
2. **Adjust scoring weights** in search algorithm
3. **Add policy aliases** (e.g., "PTO" → "leave")
4. **Implement fuzzy matching** for typos

### Extending Functionality

**Add Policy Categories**
```python
# In search_policies()
if "category:" in query:
    category = query.split("category:")[1]
    return [p for p in policies if p[0].startswith(category)]
```

**Add Filter Options**
```python
def search_policies(query, policies, department=None):
    # Filter by department if provided
    if department:
        policies = {k: v for k, v in policies.items() 
                    if f"department: {department}" in v}
    # ... rest of search
```

**Add Response Templates**
```python
def format_answer(policies, query_category):
    template = answer_templates.get(query_category, default_template)
    return template.format(policies=policies)
```

---

## 🚀 Deployment Options

### Option 1: CLI Tool
```bash
alias ask-hr='python3 /path/to/hr_agent_demo.py'
ask-hr "Can I work from home?"
```

### Option 2: Web Service
```python
from flask import Flask
app = Flask(__name__)

@app.route('/ask', methods=['POST'])
def ask_question():
    question = request.json['question']
    answer = get_relevant_answer(question, load_policies())
    return {'answer': answer}
```

### Option 3: Slack Bot
```python
from slack_bolt import App
app = App(token=token, signing_secret=secret)

@app.message("@hr-bot")
def handle_hr_questions(message, say):
    question = message['text'].replace('@hr-bot', '').strip()
    answer = get_relevant_answer(question, load_policies())
    say(answer)
```

### Option 4: Email Handler
```python
def handle_email(email):
    question = email.body
    answer = get_relevant_answer(question, load_policies())
    send_email(email.from_addr, answer)
```

---

## 🔐 Security Considerations

### API Key Management
```python
# ✅ Good: Environment variable
api_key = os.getenv("ANTHROPIC_API_KEY")

# ❌ Bad: Hardcoded
api_key = "sk-ant-..."

# ✅ Good: From .env file
from dotenv import load_dotenv
load_dotenv()
```

### Input Validation
```python
def validate_question(question: str) -> bool:
    if len(question) > 1000:
        return False
    if not isinstance(question, str):
        return False
    return True
```

### Rate Limiting
```python
from functools import wraps
import time

def rate_limit(max_per_minute=30):
    def decorator(func):
        last_called = [0.0]
        min_interval = 60.0 / max_per_minute
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_called[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## 📊 Performance Optimization

### Caching Policies
```python
import functools

@functools.lru_cache(maxsize=1)
def load_policies():
    # Load once, cache result
    policies = {}
    for file in Path("policies").glob("*.md"):
        with open(file) as f:
            policies[file.stem] = f.read()
    return policies
```

### Async API Calls
```python
import asyncio
import anthropic

async def run_agent_async(question):
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-5-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": question}]
    )
    return response
```

### Batch Processing
```python
def answer_batch_questions(questions):
    policies = load_policies()
    return [get_relevant_answer(q, policies) for q in questions]
```

---

## 📈 Monitoring & Analytics

### Log Searches
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_policies(query, policies):
    logger.info(f"Search query: {query}")
    results = # ... search logic
    logger.info(f"Found {len(results)} matches")
    return results
```

### Track Popular Questions
```python
from collections import Counter

question_counts = Counter()

def track_question(question):
    question_counts[question] += 1
    
# Get top 10 questions
top_10 = question_counts.most_common(10)
```

### Monitor API Usage
```python
import time

api_calls = []

def track_api_call(duration):
    api_calls.append({
        'timestamp': time.time(),
        'duration': duration,
        'cost': duration * COST_PER_SECOND
    })
```

---

## 🐛 Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In agent
logger.debug(f"Loaded {len(policies)} policies")
logger.debug(f"Search results: {results}")
```

### Print Search Scores
```python
def search_policies(query, policies, debug=False):
    results = []
    for policy_name, content in policies.items():
        score = calculate_score(query, policy_name, content)
        if debug:
            print(f"{policy_name}: {score}")
        results.append((policy_name, content, score))
    # ...
```

### Test with Sample Data
```python
def test_with_sample():
    policies = {
        "test": "Annual leave: 20 days. Sick leave: 10 days."
    }
    result = get_relevant_answer("How much leave?", policies)
    print(result)
```

---

## 📚 Resources

- [Anthropic API Docs](https://docs.anthropic.com)
- [Claude Model Guide](https://docs.anthropic.com/claude/reference)
- [Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [Tool Use Guide](https://docs.anthropic.com/claude/guide/tool-use)

---

## ✅ Development Checklist

- [ ] All tests passing (`python3 test_agent.py`)
- [ ] Demo works standalone (`python3 hr_agent_demo.py`)
- [ ] Full agent works with API key
- [ ] Policies load correctly
- [ ] Search accuracy acceptable
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] No hardcoded secrets
- [ ] Error handling in place
- [ ] Performance acceptable

---

**Happy coding! 🚀**
