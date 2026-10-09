# HR Policy Agent - Architecture

## Overview

The HR Policy Agent is a conversational AI system that uses Claude to answer employee questions about company policies. It follows a simple but effective architecture that prioritizes accuracy, context, and user experience.

## System Architecture

```
┌─────────────────────────────────────────┐
│         Employee/User                   │
│   (Interactive or Command Line)         │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│         agent.py                        │
│  - Chat interface                       │
│  - Question handler                     │
│  - Conversation manager                 │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│    Policy Context Loading               │
│  Load all policies/ *.md files          │
│  Build system prompt with context       │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│         llm.py                          │
│  Thin wrapper around Claude API         │
│  Message management                     │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│   Anthropic Claude API                  │
│   (claude-sonnet-5-5 by default)        │
└─────────────────────────────────────────┘
```

## Component Details

### 1. `agent.py` - Main Agent Logic

**Responsibilities:**
- Load policies from `policies/` directory
- Build system prompt with policy context
- Manage conversation state
- Handle both interactive and single-question modes
- Maintain conversation history

**Key Functions:**
- `load_policies()`: Reads all `.md` files from `policies/` directory
- `create_system_prompt()`: Wraps policy context in agent instructions
- `chat_with_agent()`: Interactive conversation loop
- `answer_question()`: Single-question mode

**Design Pattern:**
```python
# Load once at startup
policies = load_policies()

# Per request
system_prompt = create_system_prompt(policies)
response = llm.complete(system=system_prompt, messages=messages)
```

### 2. `llm.py` - API Wrapper

**Responsibilities:**
- Abstract Claude API calls
- Lazy import of anthropic library
- Response parsing

**Why a wrapper?**
- Keeps API logic centralized
- Makes testing easier (can be mocked)
- Allows easy model switching via `MODEL` env var
- Extracts text from response objects

**Implementation:**
```python
def complete(system, messages, tools=None, max_tokens=1024):
    """Return raw Messages API response"""
    client = anthropic.Anthropic()
    return client.messages.create(...)

def text_of(response):
    """Extract text content from response"""
    return "".join(b.text for b in response.content if b.type == "text")
```

### 3. `policies/` - Policy Storage

**Structure:**
```
policies/
├── leave.md          # Annual, sick, parental leave
├── remote-work.md    # Remote work allowances and rules
├── equipment.md      # Device refresh and security
├── travel.md         # Travel policies
└── expenses.md       # Expense submission rules
```

**Format:** Standard markdown with sections and clear language.

**Automatic Discovery:** All `.md` files are loaded, making it easy to add policies without code changes.

## Data Flow

### Interactive Chat Flow

```
User Input
    ↓
[Add to messages history]
    ↓
Call: llm.complete(system_prompt, messages)
    ↓
Claude processes messages with policy context
    ↓
Response generated
    ↓
[Add to messages history]
    ↓
Display to user
    ↓
Loop or exit
```

### Single Question Flow

```
Command line argument
    ↓
Create messages: [{role: "user", content: question}]
    ↓
Call: llm.complete(system_prompt, messages)
    ↓
Claude generates response
    ↓
Print and exit
```

## System Prompt Structure

The system prompt has three key parts:

```
1. ROLE & PURPOSE
   "You are a helpful HR policy assistant..."

2. INSTRUCTIONS
   "When answering questions:"
   - Refer to policy documentation
   - Be specific and cite sections
   - Handle out-of-scope questions clearly

3. POLICY CONTEXT
   [All policies concatenated]
```

Example generated prompt:
```
You are a helpful HR policy assistant. Your role is to answer 
employee questions about company HR policies accurately and clearly.

When answering questions:
- Refer directly to the policy documentation provided
- Be specific and cite relevant policy sections
- If information is not covered in the policies, say so clearly
...

## leave.md

# Leave policy (v3, effective 1 April 2026)
## Annual leave
Full-time employees accrue 20 days of annual leave per year...
```

## Advanced Feature: Tool Use

The `agent_with_tools.py` extends the base agent with structured tool calls:

```
User Query
    ↓
Agent considers available tools
    ↓
┌─ Returns text answer? → Send to user
│
└─ Calls tool? → Execute tool handler
      ↓
   Get structured data
      ↓
   Add to messages with tool result
      ↓
   Call API again for final response
      ↓
   Send to user
```

**Available Tools:**
1. `get_employee_leave_balance` - Query HR system
2. `get_policy_version` - Get policy metadata

**Implementation Pattern:**
```python
# Define tool schema
TOOLS = [{
    "name": "get_employee_leave_balance",
    "description": "...",
    "input_schema": {...}
}]

# Include in API call
response = llm.complete(
    system=system_prompt,
    messages=messages,
    tools=TOOLS  # <-- Pass available tools
)

# Handle tool calls
if response.content[0].type == "tool_use":
    result = handle_tool_call(tool_name, tool_input)
```

## Conversation State Management

**Per-Session:**
- Messages list maintains history
- Enables context awareness
- Supports follow-up questions

**Across Sessions:**
- No persistent state
- Each session is independent
- Stateless design for scalability

**For Production Use:**
```python
# Add persistence if needed
def save_conversation(messages, session_id):
    """Store conversation in database"""
    db.store(session_id, messages)

def load_conversation(session_id):
    """Restore conversation history"""
    return db.get(session_id)
```

## Error Handling

**Policy Loading Errors:**
```python
try:
    policies = load_policies()
except FileNotFoundError:
    print("No policies/ directory found")
    sys.exit(1)
```

**API Errors:**
```python
try:
    response = llm.complete(...)
except anthropic.APIError as e:
    print(f"API error: {e}")
```

**Input Validation:**
```python
if not user_input.strip():
    continue  # Skip empty inputs
```

## Performance Considerations

1. **Policy Loading:** Done once at startup
   - Time: < 100ms for typical policy set
   - Memory: ~10-50 KB for all policies

2. **API Calls:** 
   - Latency: 1-3 seconds typical
   - Cost: ~$0.01 per conversation turn

3. **Memory Usage:**
   - Conversation history grows with message count
   - For production, consider pagination/summarization

## Testing Strategy

**Unit Tests** (`test_agent.py`):
- Policy loading correctness
- System prompt generation
- Mocked LLM calls
- Real LLM integration (when API key available)

**Manual Testing:**
- Interactive chat sessions
- Various question types
- Follow-up questions
- Out-of-scope queries

## Extensibility

### Adding New Policies
Simply create a new `.md` file in `policies/`:
```bash
echo "# New Policy" > policies/new-policy.md
```

### Customizing Agent Behavior
Edit `create_system_prompt()`:
```python
def create_system_prompt(policies_context):
    # Add your custom instructions here
    return f"Custom instructions\n\n{policies_context}"
```

### Adding New Tools
Extend `TOOLS` list in `agent_with_tools.py`:
```python
TOOLS.append({
    "name": "new_tool",
    "description": "...",
    "input_schema": {...}
})
```

### Integration Points
```python
# Connect to HR system
def get_employee_leave_balance(employee_id):
    # Replace with actual API call
    return hr_api.get_leave_balance(employee_id)

# Add to database
def save_feedback(message_id, rating):
    # Replace with database call
    db.store(message_id, rating)
```

## Deployment Considerations

### For Development
```bash
python3 agent.py
```

### For Production
- Add logging and monitoring
- Implement rate limiting
- Add authentication
- Store conversation logs (compliance)
- Use async/await for scaling
- Add API response caching

### Scaling Options
1. **Web API** - FastAPI wrapper
   ```python
   @app.post("/ask")
   def ask_question(question: str):
       return {"answer": answer_question(question, policies)}
   ```

2. **Async Agent** - Handle multiple users
   ```python
   async def answer_question_async(question):
       return await llm.complete_async(...)
   ```

3. **Managed Agent** - Use Anthropic's agent infrastructure
   ```python
   # Deploy to Anthropic's managed environment
   ```

## Security

- **API Key:** Stored in environment variable
- **Policies:** Read from trusted local files
- **User Input:** No injection risks (sent as messages)
- **Tool Handlers:** Should validate inputs
- **Conversation Logs:** Consider encryption if stored

## Costs

Typical usage with Claude Sonnet 5.5:
- Short question: ~$0.005
- Multi-turn conversation (5 turns): ~$0.05
- Monthly usage (100 conversations): ~$5-10

See `llm.py` `MODEL` variable for cost/quality tradeoffs.
