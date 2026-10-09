# 🎯 HR Policy Agent - START HERE

Welcome! This document will get you up and running in 2 minutes.

## What Is This?

An **HR Policy Agent** — a Python chatbot powered by Claude that answers employee questions about company HR policies.

Employees ask questions like:
- "How much annual leave do I get?"
- "Can I work from overseas?"
- "What's the expense limit?"

The agent answers with information **directly from your HR policies**.

## 3-Step Quick Start

### Step 1: Install (30 seconds)
```bash
pip install -r requirements.txt
```

### Step 2: Set API Key (10 seconds)
```bash
export ANTHROPIC_API_KEY=your-api-key-here
```

### Step 3: Run (1 minute)
```bash
python3 hr_agent.py
```

Then ask a question:
```
You: How many days of leave do I get?
Agent: Based on the Leave policy, full-time employees accrue 20 days of 
annual leave per year, pro-rated for part-time staff...
```

**That's it! You're done.** Type `exit` to quit.

---

## 📂 Project Structure

```
HR Policy Agent
├── 💻 Code (for developers)
│   ├── hr_agent.py         ← Main agent (run this!)
│   ├── example_usage.py    ← Use as a library
│   └── test_agent.py       ← Test suite
│
├── 📚 Documentation (for everyone)
│   ├── 00-START-HERE.md    ← You are here
│   ├── INDEX.md            ← Full navigation guide
│   ├── QUICKSTART.md       ← 2-minute setup
│   ├── README.md           ← Full guide
│   └── ARCHITECTURE.md     ← System design
│
└── 📋 Policies (the actual HR policies)
    ├── leave.md            ← Leave entitlements
    ├── remote-work.md      ← Remote work rules
    ├── travel.md           ← Travel guidelines
    ├── equipment.md        ← Device policy
    └── expenses.md         ← Expense claims
```

---

## 🎯 Choose Your Path

### 👤 I'm an Employee
Want to ask HR questions? Just run:
```bash
python3 hr_agent.py
```
Ask anything about HR policies. Type `exit` when done.

### 👨‍💻 I'm a Developer
Want to integrate this into an app?

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) (5 min)
2. Review `example_usage.py` (the library API)
3. Use `HRPolicyAgent` class in your code

Quick example:
```python
from example_usage import HRPolicyAgent

agent = HRPolicyAgent()
answer = agent.ask("What's the travel policy?")
print(answer)
```

### 📊 I'm an HR Manager
Want to update policies?

1. Edit `policies/leave.md`, `policies/expenses.md`, etc.
2. Restart the agent
3. Changes take effect immediately

Add a new policy? Just create a new `.md` file in `policies/` and restart.

---

## 📖 Documentation Guide

Don't know where to go? Use this:

| I want to... | Read this |
|--------------|-----------|
| Get started in 2 minutes | [QUICKSTART.md](QUICKSTART.md) |
| Understand the full system | [README.md](README.md) |
| Navigate the project | [INDEX.md](INDEX.md) |
| Integrate into my app | [ARCHITECTURE.md](ARCHITECTURE.md) + `example_usage.py` |
| Understand the code | [hr_agent.py](hr_agent.py) (well-commented) |
| Update HR policies | Edit `policies/*.md` files |
| Test everything works | `python3 test_agent.py` |

---

## ✨ What Makes This Great

✅ **Simple** — No complex RAG, no vector databases, no magic  
✅ **Fast** — ~1-2 seconds per question  
✅ **Cheap** — ~$0.01-0.03 per question  
✅ **Accurate** — Answers grounded in actual policy documents  
✅ **Easy** — 2 minutes to run  
✅ **Extensible** — Add policies by creating markdown files  
✅ **Professional** — Well-documented and tested  

---

## 🚀 Next Steps

Pick one:

1. **Just want to try it?**
   ```bash
   python3 hr_agent.py
   ```

2. **Want to test it?**
   ```bash
   python3 test_agent.py
   ```

3. **Want to understand the code?**
   - Open `hr_agent.py` (133 lines, easy to read)
   - Open [ARCHITECTURE.md](ARCHITECTURE.md)

4. **Want to integrate it?**
   - Read [ARCHITECTURE.md](ARCHITECTURE.md)
   - Look at `example_usage.py`
   - Use the `HRPolicyAgent` class

5. **Want full docs?**
   - Start with [INDEX.md](INDEX.md)
   - Then read [README.md](README.md)

---

## ❓ Common Questions

**Q: What if I don't have an API key?**  
A: Get one from [anthropic.com](https://console.anthropic.com)

**Q: Can employees use this?**  
A: Yes! Just run `python3 hr_agent.py` and share the URL or run it on a shared server.

**Q: Can I integrate this into my intranet?**  
A: Yes! Use the `HRPolicyAgent` class from `example_usage.py`.

**Q: What if policies change?**  
A: Edit the `.md` files in `policies/` and restart the agent.

**Q: Is my data secure?**  
A: Policies are stored locally. Questions are sent to Claude API. No data is stored permanently.

---

## 📞 Need Help?

1. **Getting started**: Read [QUICKSTART.md](QUICKSTART.md)
2. **Understanding it**: Read [README.md](README.md)
3. **System design**: Read [ARCHITECTURE.md](ARCHITECTURE.md)
4. **Troubleshooting**: See "Troubleshooting" in [README.md](README.md)

---

## Ready? Let's Go!

```bash
# 1. Install
pip install -r requirements.txt

# 2. Set API key
export ANTHROPIC_API_KEY=your-api-key-here

# 3. Run
python3 hr_agent.py

# 4. Ask questions!
```

**That's it!** 🎉

For more details, see:
- [INDEX.md](INDEX.md) — Full navigation guide
- [QUICKSTART.md](QUICKSTART.md) — 2-minute quick start
- [README.md](README.md) — Complete documentation
