# HR Policy Agent - Run Checklist

## Pre-Run Setup (One-time)

- [ ] Python 3.8+ installed (`python --version`)
- [ ] Clone/download this repository
- [ ] Navigate to project directory: `cd hr-policy-agent`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Have Anthropic API key ready (get from https://console.anthropic.com)

## Environment Setup (Per session)

- [ ] Set API key: `export ANTHROPIC_API_KEY=sk-ant-...`
- [ ] Verify key is set: `echo $ANTHROPIC_API_KEY` (should show first 20 chars)
- [ ] Confirm policies exist: `ls -la policies/`
  - Should show: equipment.md, expenses.md, leave.md, remote-work.md, travel.md

## Run Options

### Option 1: Interactive Conversation (Recommended)

```bash
python hr_agent.py
```

✓ Best for: Testing, exploring, learning  
✓ Multi-turn support: Yes (maintains context)  
✓ Cost: ~$0.0015 first query, ~$0.00015 subsequent  
✓ Exit with: `exit`, `quit`, or Ctrl+D

**Test these conversations:**

1. Simple question:
   ```
   Your question: How many days of annual leave?
   ```
   Expect: "20 days + 5 carryover..."

2. Follow-up:
   ```
   Your question: Can I carry over more than 5?
   ```
   Expect: References the same policy, knows context

3. Out-of-policy question:
   ```
   Your question: Do you offer pet insurance?
   ```
   Expect: "Not covered by current policies..."

### Option 2: Single Question from CLI

```bash
python hr_agent.py "How much annual leave do I get?"
```

✓ Best for: Scripting, automation, quick checks  
✓ Multi-turn support: No (single question only)  
✓ Cost: ~$0.0015 (no cache reuse)  
✓ Output: Answer printed, exits immediately

**Test these commands:**

```bash
# Straightforward question
python hr_agent.py "What is the equipment policy?"

# Question outside policies
python hr_agent.py "What is the office dress code?"

# Multi-part question
python hr_agent.py "How much leave can I carry over and when does it expire?"
```

### Option 3: Run Test Suite

```bash
python test_agent.py
```

✓ Best for: Validation, regression testing, demos  
✓ Multi-turn support: Yes (maintains history across 7 Qs)  
✓ Cost: ~$0.002 (one cache creation, then 6 cache hits)  
✓ Output: Q&A pairs to review  

**What to verify:**
- [ ] All 7 questions produce answers
- [ ] Answers cite their policy sources
- [ ] Q7 ("pet insurance") is escalated to HR
- [ ] Follow-ups maintain context (e.g., Q2 references Q1)

## Expected Outputs

### Interactive Mode

```
============================================================
HR POLICY ASSISTANT
============================================================
Ask me about any HR policies. Type 'exit' or 'quit' to end.

Your question: How much annual leave do full-time employees get?
Assistant: According to the leave policy (v3, effective 1 April 2026), 
full-time employees accrue 20 days of annual leave per year. This is 
pro-rated for part-time staff.

Additionally, you can carry over up to 5 unused days to the next year; 
any remaining days lapse on March 31st.

**Source: leave.md**

[Cache stats: created=1000, read=0]

Your question: exit
Thank you for using the HR Policy Assistant. Goodbye!
```

### CLI Mode

```
Q: How much annual leave do I get?

Answer:
According to the leave policy, full-time employees accrue 20 days 
of annual leave per year...

[Cache stats: created=1000, read=0]
```

### Test Suite

```
Loading policies...

Q: How many days of annual leave do I get as a full-time employee?
A: According to the leave policy...
[Cache stats: created=1000, read=0]

------------------------------------------------------------

Q: What's the process for meal expenses when I travel for work?
A: According to the expenses policy...
[Cache stats: created=0, read=1000]

------------------------------------------------------------

...
(5 more Q&A pairs)
```

## Troubleshooting

### Error: `AuthenticationError: Incorrect API key provided`

**Cause:** API key not set or invalid  
**Fix:**
```bash
export ANTHROPIC_API_KEY=sk-ant-...  # Replace with real key
python hr_agent.py
```

**Verify:** `echo $ANTHROPIC_API_KEY` should show your key's first 20 chars

---

### Error: `FileNotFoundError: No policy files found in policies`

**Cause:** Running from wrong directory or policies/ folder missing  
**Fix:**
```bash
# Ensure you're in the project root
pwd  # Should end with: /hr-policy-agent

# Check policies exist
ls policies/
# Should show: equipment.md, expenses.md, leave.md, remote-work.md, travel.md
```

---

### Error: `ModuleNotFoundError: No module named 'anthropic'`

**Cause:** Dependencies not installed  
**Fix:**
```bash
pip install -r requirements.txt
```

**Verify:** `python -c "import anthropic; print(anthropic.__version__)"`

---

### No output after typing question

**Cause:** Agent is thinking (normal, takes 1-2 seconds)  
**Fix:** Wait 2-3 seconds. If still stuck:
- Press Ctrl+C to cancel
- Check API key: `echo $ANTHROPIC_API_KEY`
- Check internet connection
- Try a simpler question

---

### Cache stats show only `created` tokens, never `read`

**This is normal!** Cache only hits on follow-up questions in the same session.
- Q1: `created=1000, read=0` (first query, builds cache)
- Q2: `created=0, read=1000` (cache hit, reuses policies)
- Q3: `created=0, read=1000` (cache still valid)

If you exit and restart, cache expires after 5 minutes, so Q1 of new session will create again.

---

## Performance Checklist

- [ ] First question answers in <2 seconds? (Normal: 1-2s for network + inference)
- [ ] Follow-up questions answer in <500ms? (Cache hit is fast)
- [ ] Agent cites policy sources? (e.g., "Source: leave.md")
- [ ] Questions outside policies are escalated? (e.g., "contact HR")
- [ ] Multi-turn conversation works? (Follow-ups reference previous answers)

If any check fails:
- [ ] Verify API key is valid (test with single question)
- [ ] Check internet connection (`ping google.com`)
- [ ] Restart Python (`exit`, then `python hr_agent.py` again)
- [ ] Check Anthropic API status (https://status.anthropic.com)

## Cost Verification

Track spending:
```bash
# After running some questions, check your Anthropic usage dashboard:
# https://console.anthropic.com/account/billing/overview

Expected monthly cost for 100 q/day:
  100 q/day × 30 days = 3000 queries/month
  50% are first-time (uncached) @ $0.0015 = $2.25
  50% are follow-ups (cached) @ $0.00015 = $0.23
  Total: ~$2.50/month (rough estimate)
```

## Success Criteria

✅ Agent is working correctly if:

1. You can ask HR policy questions interactively
2. You get answers that cite which policy they came from
3. Follow-up questions maintain context
4. Questions outside policies are escalated to HR
5. Cache stats show savings on subsequent questions
6. No crashes or errors (other than API key issues)

🎉 You're done! The agent is ready to use.

---

## Next Steps

### Immediate (if working):
- [ ] Test with your own questions
- [ ] Share QUICKSTART.md with users
- [ ] Add agent URL/access instructions to internal wiki

### Short-term (1-2 weeks):
- [ ] Deploy to Slack as `/ask-hr` command
- [ ] Add policy versioning (update dates in policies)
- [ ] Create FAQ from top questions

### Medium-term (1-2 months):
- [ ] Set up usage analytics (log questions, track popularity)
- [ ] Implement feedback loop (thumbs up/down on answers)
- [ ] Train HR staff on how it works

### Long-term (as needed):
- [ ] Web interface for non-Slack users
- [ ] Integration with HR system (look up balances, submit requests)
- [ ] Multi-language support
- [ ] Mobile app

---

**Last updated:** 2024-10-09  
**Agent version:** 1.0  
**Policies version:** v3 (effective 1 April 2026)
