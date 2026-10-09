# Quick Start

Get the HR policy agent running in 3 steps.

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Set API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

(Get your key from [console.anthropic.com](https://console.anthropic.com))

## 3. Run the agent

**Interactive mode (ask questions manually):**
```bash
python3 agent.py
```

**Example output:**
```
HR Policy Assistant
==================================================
Ask questions about company HR policies. Type 'quit' to exit.

Q: How many days of annual leave do I get?

Retrieving policies...
A: According to the Leave policy, full-time employees accrue 20 days of annual leave per year. Part-time staff receive a pro-rated amount. You can carry over up to 5 unused days to the next year; any remaining days lapse on 31 March. (from Leave policy)

Q: Can I work from home?
...
```

**Use as a library:**
```python
from agent import answer_question

answer = answer_question("How much parental leave can I take?")
print(answer)
```

**Run examples:**
```bash
python3 examples.py
```

**Run tests:**
```bash
python3 -m pytest test_agent.py -v
```

## Next steps

- **Integrate:** See [INTEGRATION.md](INTEGRATION.md) for Slack, web, email options
- **Extend:** Add policies to `policies/` directory (they're auto-loaded)
- **Learn:** Read [DESIGN.md](DESIGN.md) for architecture details
- **Debug:** Check retrieved policies in `agent.py` → `build_system_prompt()` function

## Troubleshooting

**"Module not found: anthropic"**
```bash
pip install anthropic
```

**"ANTHROPIC_API_KEY not set"**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**Agent gives wrong answers**
1. Check if the policy text is correct in `policies/*.md`
2. Check retrieval: uncomment debug print in `retrieve_relevant_policies()` to see which policies were retrieved
3. Try a different model: `MODEL=claude-opus-5-5 python3 agent.py`

---

**Done?** Deploy to Slack, web, or email using guides in [INTEGRATION.md](INTEGRATION.md).
