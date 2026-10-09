# HR Policy Agent - Quick Start Guide

## 🎯 Get Started in 30 Seconds

### No Setup Required - Try the Demo Now

```bash
python3 hr_agent_demo.py
```

This will show you example HR policy questions and answers.

### Ask Your Own Question

```bash
python3 hr_agent_demo.py "Your question here"
```

**Examples:**
```bash
python3 hr_agent_demo.py "How much annual leave do I get?"
python3 hr_agent_demo.py "Can I work from home?"
python3 hr_agent_demo.py "What's the laptop refresh policy?"
```

---

## 🤖 Full Agent with Claude AI (Optional)

For smarter, more conversational responses using Claude:

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Your API Key
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### 3. Run the Agent
```bash
python3 hr_agent.py "Your question"
```

---

## 📚 What Can the Agent Answer?

The agent knows about:

| Topic | Examples |
|-------|----------|
| **Leave** | Annual leave, sick leave, parental leave |
| **Remote Work** | Working from home, overseas work |
| **Expenses** | Claiming meals, receipts, approval limits |
| **Travel** | Booking flights, approval process |
| **Equipment** | Laptop refresh, lost devices |

---

## ✅ Run Tests

Verify everything is working:

```bash
python3 test_agent.py
```

---

## 📖 Full Documentation

For more details, see [README.md](README.md)

---

## 🆘 Common Questions

**Q: Do I need an API key?**
A: No! The demo version works without one. The full agent with Claude requires an API key.

**Q: Where's the policy documentation?**
A: Check the `policies/` folder for all HR policies as markdown files.

**Q: Can I add new policies?**
A: Yes! Just add a new `.md` file to the `policies/` folder and the agent will pick it up automatically.

**Q: How accurate is it?**
A: The agent searches actual policy documents and returns exact excerpts, so it's very accurate.

---

**Need help?** Contact HR or check the README.md file.
