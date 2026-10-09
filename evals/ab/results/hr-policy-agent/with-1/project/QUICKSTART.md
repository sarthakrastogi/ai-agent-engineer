# Quick Start

## 1. Install

```bash
pip install -r requirements.txt
```

## 2. Set API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
# Edit .env with your API key
```

## 3. Run

**Interactive:**
```bash
python agent.py
```

**Single question:**
```bash
python agent.py "How much annual leave do I get?"
```

**Example questions:**
```bash
python example.py
```

## 4. Test

```bash
pytest test_agent.py -v
```

## 5. Use in code

```python
from agent import answer_question

answer = answer_question("Can I work from home?")
print(answer)
```

## That's it!

For more details, see:
- `README.md` — Full documentation
- `DESIGN.md` — Architecture and design decisions
