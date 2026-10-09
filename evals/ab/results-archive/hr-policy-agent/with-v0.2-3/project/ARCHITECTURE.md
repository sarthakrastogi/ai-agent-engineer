# HR Policy Agent - Architecture

## System Design

```
┌─────────────────────────────────────────────────────────────┐
│                   Employee Question                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │   HR Policy Agent (hr_agent.py)   │
         │   - Loads policies from disk      │
         │   - Manages conversation history  │
         │   - Calls Claude API              │
         └────────┬──────────────────────────┘
                  │
         ┌────────┴──────────────────────────┐
         │                                   │
         ▼                                   ▼
   ┌──────────────┐                  ┌──────────────────┐
   │  Policies    │                  │ Claude API Call  │
   │ (markdown)   │                  │   (claude-opus-  │
   │              │                  │     5-5)         │
   │ • leave.md   │                  │                  │
   │ • remote...  │     ──────────►  │ System Prompt:   │
   │ • travel.md  │                  │ - All policies   │
   │ • equipment. │                  │ - Instructions   │
   │ • expenses.  │                  │                  │
   └──────────────┘                  │ Messages:        │
                                     │ - User question  │
                                     │ - History        │
                                     └─────────┬────────┘
                                               │
                                               ▼
                                     ┌─────────────────────┐
                                     │ Policy-backed Answer│
                                     │ (with citations)    │
                                     └─────────┬───────────┘
                                               │
                                               ▼
                                     ┌─────────────────────┐
                                     │ Return to Employee  │
                                     └─────────────────────┘
```

## Components

### 1. **Core Agent** (`hr_agent.py`)
- **Purpose**: Main interactive application for employees
- **Key Functions**:
  - `load_policies()`: Reads all MD files from policies/ directory
  - `create_system_prompt()`: Builds prompt with all policies embedded
  - `run_agent()`: Interactive CLI loop

- **Flow**:
  1. Load all policy files as strings
  2. Build comprehensive system prompt
  3. Loop: get user input → call Claude → save history → display response

### 2. **Test Suite** (`test_agent.py`)
- **Purpose**: Demonstrate functionality with predefined questions
- **Use Cases**:
  - Verify agent is working after updates
  - Show capabilities to stakeholders
  - Regression testing

### 3. **Library Interface** (`example_usage.py`)
- **Purpose**: Programmatic API for integration
- **Key Class**: `HRPolicyAgent`
  - Initialize with policy directory
  - `ask(question)` method for individual queries
  - `reset_conversation()` for new conversations
  - Maintains conversation history automatically

### 4. **Policy Documents** (`policies/`)
- **Format**: Markdown files, one per topic
- **Content**:
  - leave.md - Annual/sick/parental leave
  - remote-work.md - Remote work terms
  - travel.md - Business travel guidelines
  - equipment.md - Device policy
  - expenses.md - Expense claims rules

## Data Flow

### Single Query
```
Question → Load System Prompt → Call Claude → Answer
```

### Multi-turn Conversation
```
Q1 → Add to history
↓
A1 ← Save to history
↓
Q2 → Append to history
↓
A2 ← Claude uses full history for context
↓
Q3 → And so on...
```

## Key Design Decisions

### 1. **System Prompt Strategy**
- All policies embedded in system prompt (not retrieved per-call)
- **Pro**: Guarantees consistency, no retrieval latency
- **Con**: Fixed policies at agent startup; updates require restart
- **Why**: For small policy set (~1KB), simplicity > flexibility

### 2. **Conversation History**
- Maintained in memory, per session
- Allows multi-turn conversations naturally
- Reset with `reset_conversation()`
- **Why**: Employees expect context like normal chat

### 3. **No Tool Calls**
- Agent doesn't call external tools (no database, no file reads)
- Only calls Claude API
- **Why**: All needed info (policies) already in prompt

### 4. **Citation by Design**
- System prompt instructs Claude to cite policy sections
- No fancy citation markup needed
- **Why**: Claude already trained to do this well

## Extension Points

### Add New Policy
1. Create `policies/new-topic.md`
2. Restart agent (reloads automatically)
3. Done!

### Integrate into Web App
1. Use `HRPolicyAgent` class from `example_usage.py`
2. Call `agent.ask(question)` from your backend
3. Return response to frontend

### Add Approval Workflows
1. Detect policy-affected questions
2. Route to HR for pre-approval
3. Return approved response

### Add Logging/Analytics
1. Wrap `agent.ask()` with logging
2. Log questions, answers, user IDs
3. Analyze common questions for FAQ

## Limitations & Future Work

### Current Limitations
- Policies fixed at startup (no live updates)
- No database of employee-specific info (vacation balance, etc.)
- No approval workflows (just answers)
- No audit trail of who asked what
- Single-threaded (processes questions sequentially)

### Potential Enhancements
- **Dynamic policies**: Load from database, update without restart
- **Personalization**: Query employee database for context (e.g., "How many days left?")
- **Approvals**: Suggest workflows for policy-affecting requests
- **Analytics**: Track questions, identify FAQ candidates
- **Multi-language**: Translate policies and responses
- **Integration**: Connect to HR systems, calendar, expense tools

## Performance Considerations

- **Latency**: ~1-2 seconds per question (Claude API call)
- **Cost**: ~$0.01-0.03 per question (typical prompt size)
- **Scalability**: Single agent is synchronous; use job queue for many concurrent users
- **Context window**: Conversation history limited by token budget (~100KB for typical 1-turn average)

## Security & Privacy

- **API Key**: Must be set in environment (`ANTHROPIC_API_KEY`)
- **Data**: Policies loaded from local files, not transmitted unnecessarily
- **User Data**: Conversation history in memory only, not persisted
- **Scope**: Agent can only answer from policy; cannot perform actions
