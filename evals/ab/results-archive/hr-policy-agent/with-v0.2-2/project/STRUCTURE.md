# Project Structure

```
hr-policy-agent/
│
├── 📄 README.md                    ← START HERE: User guide and feature overview
├── 📄 QUICKSTART.md               ← 5-minute setup guide
├── 📄 IMPLEMENTATION_SUMMARY.md    ← What was built and how
├── 📄 DEVELOPMENT.md              ← Technical deep-dive for developers
├── 📄 CONFIG.md                   ← Configuration and tuning options
├── 📄 STRUCTURE.md                ← This file
│
├── 🐍 AGENT FILES (Choose one to run)
│   ├── hr_agent.py                (Simple: 100 lines, no dependencies)
│   ├── hr_agent_advanced.py       (Feature-rich: Commands, history, persistence)
│   └── llm.py                     (Existing helper file)
│
├── 🧪 TESTING & EXAMPLES
│   ├── test_agent.py              (Automated tests for 6 common questions)
│   └── example_usage.py           (4 usage patterns + integration examples)
│
├── 📚 POLICIES (Auto-loaded by agent)
│   ├── leave.md                   (Annual, sick, parental leave)
│   ├── remote-work.md             (Work from home & overseas)
│   ├── travel.md                  (Travel approvals & booking)
│   ├── equipment.md               (Device management & refresh)
│   └── expenses.md                (Claims, limits, approval)
│
└── ⚙️ CONFIGURATION
    ├── requirements.txt           (Dependencies: just "anthropic")
    └── .chat_history.json        (Generated: conversation history)
```

## File Guide

### For Users
- **README.md** - What is this? What can it do?
- **QUICKSTART.md** - How do I get started in 5 minutes?
- **hr_agent.py** - Run this for simple interactive chat
- **hr_agent_advanced.py** - Run this for more features

### For Developers
- **DEVELOPMENT.md** - How does it work? How do I extend it?
- **CONFIG.md** - How do I customize it?
- **example_usage.py** - How do I use it as a library?
- **test_agent.py** - How do I test it?

### For Decision Makers
- **IMPLEMENTATION_SUMMARY.md** - What was built and why?
- **CONFIG.md** - Deployment and scaling options

## Quick Decision Tree

```
Q: I want to try the agent quickly
└─> Run: python3 hr_agent.py

Q: I want features like /save and /load
└─> Run: python3 hr_agent_advanced.py

Q: I want to test it's working
└─> Run: python3 test_agent.py

Q: I want to use it in my app
└─> Import from: example_usage.py

Q: I want to understand the code
└─> Read: DEVELOPMENT.md

Q: I want to customize behavior
└─> Edit: build_system_prompt() or see CONFIG.md

Q: I want to add a new policy
└─> Create: policies/my_policy.md (no code changes!)

Q: I want to deploy to production
└─> See: CONFIG.md (Deployment section)
```

## File Sizes & Complexity

| File | Lines | Complexity | Purpose |
|------|-------|-----------|---------|
| hr_agent.py | 100 | Low | Simple interactive agent |
| hr_agent_advanced.py | 200 | Medium | Production-ready agent |
| test_agent.py | 100 | Low | Test suite |
| example_usage.py | 150 | Medium | Usage examples & API |
| README.md | 200 | Low | Documentation |
| DEVELOPMENT.md | 400 | Medium | Technical guide |

## Getting Started Paths

### Path 1: Quick Demo (5 min)
1. `pip install -r requirements.txt`
2. `export ANTHROPIC_API_KEY="..."`
3. `python3 hr_agent.py`
4. Ask a question!

### Path 2: Learn the Code (30 min)
1. Read README.md
2. Skim IMPLEMENTATION_SUMMARY.md
3. Run `python3 example_usage.py`
4. Read example_usage.py code

### Path 3: Production Deployment (1 hour)
1. Read CONFIG.md (Deployment section)
2. Choose deployment option
3. Configure environment variables
4. Deploy using template

### Path 4: Customize for Your Company (30 min)
1. Add your policies to `policies/` directory
2. Edit system prompt in agent file if needed
3. Test with `python3 test_agent.py`
4. Deploy

## Common Tasks

| Task | File(s) | Time |
|------|---------|------|
| Run the agent | hr_agent.py | 1 min |
| Add a policy | policies/new.md | 5 min |
| Change model/cost | CONFIG.md | 10 min |
| Integrate with web app | example_usage.py | 15 min |
| Deploy to production | CONFIG.md | 30 min |
| Understand architecture | DEVELOPMENT.md | 30 min |
| Extend with features | DEVELOPMENT.md | 1 hour |

## Documentation Map

```
Getting Started?
├─ QUICKSTART.md (5 min)
├─ README.md (10 min)
└─ IMPLEMENTATION_SUMMARY.md (20 min)

Want to code?
├─ example_usage.py (read code)
├─ DEVELOPMENT.md (technical)
└─ test_agent.py (test patterns)

Want to deploy?
├─ CONFIG.md (all options)
├─ DEVELOPMENT.md (integration)
└─ IMPLEMENTATION_SUMMARY.md (deployment)

Want to modify?
├─ CONFIG.md (configuration)
├─ DEVELOPMENT.md (how to extend)
└─ policies/*.md (how to update)
```

## File Dependencies

```
hr_agent.py
  └─ policies/*.md (auto-loads)
  └─ anthropic (from requirements.txt)

hr_agent_advanced.py
  └─ policies/*.md (auto-loads)
  └─ anthropic (from requirements.txt)

test_agent.py
  └─ policies/*.md (auto-loads)
  └─ anthropic (from requirements.txt)

example_usage.py
  └─ policies/*.md (auto-loads)
  └─ anthropic (from requirements.txt)
```

All agents are independent and can run separately.

## Next Steps

1. **Try it**: `python3 hr_agent.py`
2. **Understand it**: Read QUICKSTART.md
3. **Extend it**: Add policies to `policies/` directory
4. **Deploy it**: Follow CONFIG.md for your platform
5. **Monitor it**: Track usage via .chat_history.json

---

**Ready?** Start with: `python3 hr_agent.py`
