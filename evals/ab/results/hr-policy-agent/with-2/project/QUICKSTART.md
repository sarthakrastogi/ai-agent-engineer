# Quick Start Guide

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Set your API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## 3. Run the agent

### Interactive conversation
```bash
python hr_agent.py
```

Example session:
```
Your question: How much annual leave do full-time employees get?
Assistant: According to the leave policy, full-time employees accrue 20 days of annual leave per year. Part-time staff receive pro-rated amounts.

Additionally, you can carry over up to 5 unused days to the next year; any remaining days lapse on March 31st.

**Source: leave.md**

Your question: What if I want to carry over more than 5 days?
Assistant: According to the leave policy, only up to 5 unused days can be carried over to the next year. Any days beyond that 5-day allowance will lapse on March 31st. You may want to discuss taking time off before the year-end deadline with your manager if you have more than 5 days remaining.

**Source: leave.md**
```

### Ask a single question
```bash
python hr_agent.py "Can I work from overseas for 3 weeks?"
```

### Run test suite
```bash
python test_agent.py
```

## 4. What the agent can answer

✅ Questions about:
- Annual, sick, and parental leave entitlements
- Expense claims and reimbursement limits
- Remote work policies and allowances
- Travel booking and class requirements
- Equipment and laptop refresh cycles

❌ The agent will say "I don't know" or "contact HR" for:
- Benefits coverage (health insurance, etc.)
- Salary or compensation questions
- Performance reviews or promotions
- Disciplinary matters
- Anything not in the HR policies

## 5. How it works

1. **Loads all policies** from `policies/*.md` at startup
2. **Maintains conversation history** for follow-up questions
3. **Uses prompt caching** to reduce latency and cost
4. **Cites sources** so employees know where answers come from
5. **Stays strictly in policies** - won't make up answers

## 6. Example questions to try

```
"How many days of sick leave do I get per year?"
"What's the equipment policy for lost devices?"
"Do I need approval for a remote work day?"
"What class should I book for a 7-hour flight?"
"Can I get a home office allowance?"
"When is my next laptop refresh due?"
```

## Troubleshooting

**API key error:**
```
AuthenticationError: Incorrect API key provided
```
→ Check `export ANTHROPIC_API_KEY=...` is set in your terminal

**Module not found:**
```
ModuleNotFoundError: No module named 'anthropic'
```
→ Run `pip install -r requirements.txt`

**No policies found:**
```
FileNotFoundError: No policy files found in policies
```
→ Ensure you're running from the project root directory with a `policies/` folder

## Next steps

- Add more policies to `policies/` and they'll be auto-loaded
- Modify the system prompt in `hr_agent.py` for different tone
- Integrate with your HR system via additional tools
- Deploy as a Slack bot or internal web service
