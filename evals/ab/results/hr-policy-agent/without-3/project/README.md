# HR Policy Agent

A Python-based agent that answers employee questions about company HR policies. The agent searches through policy documents and provides accurate, helpful responses to common HR questions.

## 📁 Project Structure

```
hr-policy-agent/
├── hr_agent.py              # Full-featured agent with Claude API integration
├── hr_agent_demo.py         # Demo version (no API key required)
├── policies/                # HR policy documents
│   ├── leave.md            # Leave and time-off policies
│   ├── expenses.md         # Expense claim policies
│   ├── remote-work.md      # Remote work policies
│   ├── travel.md           # Travel policies
│   └── equipment.md        # Equipment policies
└── README.md               # This file
```

## 🚀 Quick Start

### Option 1: Demo Version (Recommended for Testing)

No API key required! This version demonstrates how the agent works:

```bash
# Run with example questions
python3 hr_agent_demo.py

# Ask a specific question
python3 hr_agent_demo.py "Can I work from home?"
```

### Option 2: Full Agent with Claude API

For the full agentic experience with Claude's language understanding:

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Run with example questions
python3 hr_agent.py

# Ask a specific question
python3 hr_agent.py "How much annual leave do I get?"
```

## 📋 Features

### Demo Version (`hr_agent_demo.py`)
- ✅ No API credentials required
- ✅ Instant responses
- ✅ Keyword-based policy search
- ✅ Shows all relevant policies for a question
- ✅ Perfect for demos and testing

### Full Agent (`hr_agent.py`)
- 🤖 Claude Opus 5.5 language understanding
- 🔍 Intelligent policy search with tool use
- 💬 Natural conversational responses
- 📊 Context-aware answers
- ✅ Handles complex follow-up questions

## 🎯 Example Queries

The agents can answer questions like:

```
"How much annual leave do I get?"
"Can I work remotely?"
"What's the policy on claiming meal expenses?"
"When can I get a new laptop?"
"What if I need parental leave?"
"How long do I have to submit expense claims?"
"Do I need approval to travel internationally?"
"What's the home office allowance?"
```

## 📚 Available Policies

### Leave Policy
- Annual leave: 20 days per year for full-time employees
- Sick leave: 10 days per year
- Parental leave: 26 weeks for primary carers (after 6 months service)
- Carryover: Up to 5 unused days can roll over

### Expenses Policy
- Claim deadline: Within 60 days of purchase
- Meal limits: NZD 80 per day while traveling
- Approval threshold: Claims over NZD 500 need director approval
- Receipt requirement: Itemised receipts required

### Remote Work Policy
- Remote days: Up to 3 days per week with manager agreement
- International: Requires HR and tax approval for 2+ weeks overseas
- Home office allowance: NZD 400 available once every 3 years

### Travel Policy
- Booking: All flights through TravelDesk
- Flight class: Economy for <6 hours, premium economy for longer
- Approval: Manager approval for domestic, director for international

### Equipment Policy
- Laptop refresh: Every 3 years
- Lost/stolen: Report to IT within 24 hours
- Personal devices: Email access only through Intune app

## 🔧 How It Works

### Demo Version Flow

1. Employee asks a question
2. Agent searches for keywords in policy documents
3. Matching policies are ranked by relevance
4. Relevant policy sections are returned
5. Response is formatted with policy context

### Full Agent Flow

1. Employee asks a question
2. Claude API is called with the question
3. Claude uses the `search_policies` tool to find relevant policies
4. Claude generates a natural language response
5. Response is returned to the employee

## 💻 Installation

### Requirements
- Python 3.8+
- Anthropic Python SDK (only for full agent)

### Setup

```bash
# Clone or navigate to the project
cd hr-policy-agent

# For full agent only, install the SDK
pip install anthropic

# Set your API key (for full agent)
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

## 🎮 Usage Examples

### Demo Agent
```bash
# Ask about leave
python3 hr_agent_demo.py "I need time off - what are my options?"

# Ask about travel
python3 hr_agent_demo.py "How do I book a business flight?"

# Ask about equipment
python3 hr_agent_demo.py "My laptop was stolen, what should I do?"
```

### Full Agent
```bash
# Set API key first
export ANTHROPIC_API_KEY="sk-ant-..."

# Ask about expenses
python3 hr_agent.py "How do I claim meal expenses?"

# Ask about remote work
python3 hr_agent.py "Can I work from overseas for a month?"

# Ask about equipment refresh
python3 hr_agent.py "When can I get a new laptop refresh?"
```

## 🔍 Troubleshooting

### API Key Error
```
Error: "Could not resolve authentication method"
```
**Solution:** Set the environment variable:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Module Not Found
```
ModuleNotFoundError: No module named 'anthropic'
```
**Solution:** Install the SDK:
```bash
pip install anthropic
```

### No Policies Found
If the agent can't find relevant policies, it will suggest contacting HR directly. This might mean:
- The question is outside policy scope
- The search terms don't match policy keywords
- HR may need to update the policies

## 📝 Adding New Policies

1. Create a new `.md` file in the `policies/` directory
2. Write the policy using clear section headers (##)
3. The agent will automatically pick it up

Example:
```markdown
# Health Insurance Policy
## Coverage
All employees receive comprehensive health insurance...
```

## 🚀 Extension Ideas

- Add a web interface with Flask
- Integrate with Slack for `@hr-bot` queries
- Add policy versioning and change history
- Build a FAQ builder from common questions
- Add multilingual support
- Create an admin dashboard for policy updates
- Add feedback mechanism to improve search

## 📄 License

Internal company tool - all rights reserved.

---

**Questions?** Contact the HR department or your manager.
