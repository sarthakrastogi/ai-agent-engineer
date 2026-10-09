# Integration Guide

This agent can be integrated into various systems to serve employees. Here are some practical options.

## 1. Slack Bot (Recommended for quick access)

Add the agent as a Slack app so employees can ask questions directly in Slack.

```python
# slack_bot.py
import os
from slack_bolt import App
from agent import answer_question

app = App(token=os.environ["SLACK_BOT_TOKEN"],
          signing_secret=os.environ["SLACK_SIGNING_SECRET"])

@app.message("^hr ")
def handle_hr_question(message, say):
    question = message["text"].replace("^hr ", "", 1).strip()
    if not question:
        say("Please ask a question about HR policies. Example: _hr How many days of leave do I get?_")
        return
    
    answer = answer_question(question)
    say(f"*Q:* {question}\n\n{answer}")

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
```

**Usage in Slack:**
```
@hr-bot hr How many days of annual leave do I get?
```

## 2. Web Interface (Employee portal)

Embed the agent in an internal HR portal.

```python
# web_app.py (using Flask)
from flask import Flask, request, jsonify
from agent import answer_question

app = Flask(__name__)

@app.route("/api/hr-question", methods=["POST"])
def ask_hr_question():
    data = request.json
    question = data.get("question", "").strip()
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    answer = answer_question(question)
    return jsonify({"question": question, "answer": answer})

@app.route("/", methods=["GET"])
def index():
    return """
    <html>
        <body>
            <h1>HR Policy Assistant</h1>
            <input type="text" id="question" placeholder="Ask an HR policy question...">
            <button onclick="askQuestion()">Ask</button>
            <div id="answer"></div>
            <script>
                async function askQuestion() {
                    const q = document.getElementById('question').value;
                    const resp = await fetch('/api/hr-question', {
                        method: 'POST',
                        body: JSON.stringify({question: q}),
                        headers: {'Content-Type': 'application/json'}
                    });
                    const data = await resp.json();
                    document.getElementById('answer').innerHTML = data.answer;
                }
            </script>
        </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=False)
```

## 3. Email Integration (FAQ auto-responder)

Forward HR policy emails to the agent for automated responses.

```python
# email_responder.py
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from agent import answer_question

def respond_to_email(sender_email, subject, body):
    """Send an automated response to an HR policy question."""
    
    # Extract question (remove "Fwd:", "Re:", etc.)
    question = subject.replace("Fwd:", "").replace("Re:", "").strip()
    
    # Get answer from agent
    answer = answer_question(question)
    
    # Send response
    msg = MIMEMultipart()
    msg["From"] = "hr-bot@company.com"
    msg["To"] = sender_email
    msg["Subject"] = f"Re: {subject}"
    msg.attach(MIMEText(f"Thanks for your question!\n\n{answer}"))
    
    with smtplib.SMTP("smtp.company.com") as server:
        server.send_message(msg)

# Integration with email system (e.g., mailbox listener):
# for email in mailbox.unread():
#     respond_to_email(email.sender, email.subject, email.body)
```

## 4. API Endpoint (Service for multiple clients)

Deploy the agent as a simple HTTP service.

```bash
# requirements-api.txt
flask==2.3.0
anthropic>=0.28.0

# Run:
# flask --app api.py run --port 5000
```

```python
# api.py
from flask import Flask, request, jsonify
from agent import answer_question, load_policies

app = Flask(__name__)
policies = load_policies()  # Load once on startup

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "version": "1.0"}

@app.route("/ask", methods=["POST"])
def ask():
    """POST a question, get an answer."""
    body = request.json or {}
    question = body.get("question", "").strip()
    
    if not question:
        return {"error": "question field required"}, 400
    
    try:
        answer = answer_question(question, policies)
        return {"question": question, "answer": answer}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/policies", methods=["GET"])
def list_policies():
    """List all available policies."""
    return {
        "policies": [
            {"name": name, "size": len(content)}
            for name, content in policies.items()
        ]
    }
```

**Usage:**
```bash
# Ask a question
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How many days of leave?"}'

# Check health
curl http://localhost:5000/health

# List policies
curl http://localhost:5000/policies
```

## 5. MS Teams Bot

Integrate into Microsoft Teams for enterprise deployments.

```python
# teams_bot.py (using python-botframework)
from botframework.connector import ConnectorClient
from botframework.activity import Activity, ActivityTypes
from agent import answer_question

async def on_message_activity(turn_context):
    question = turn_context.activity.text.strip()
    
    if question.lower().startswith("hr "):
        question = question[3:].strip()
        answer = answer_question(question)
        reply = Activity(
            type=ActivityTypes.message,
            text=answer
        )
        await turn_context.send_activity(reply)
```

## 6. Batch Processing (Daily FAQ digest)

Auto-respond to frequently asked questions and post a daily summary.

```python
# daily_faq.py
from agent import answer_question
import json

COMMON_QUESTIONS = [
    "How many days of annual leave do I get?",
    "Can I work from home?",
    "What's the meal allowance when travelling?",
    "When do I get a new laptop?",
]

def generate_faq_digest():
    """Generate a daily FAQ sheet."""
    digest = "# Daily HR FAQ\n\n"
    
    for q in COMMON_QUESTIONS:
        answer = answer_question(q)
        digest += f"## Q: {q}\n\n{answer}\n\n---\n\n"
    
    # Post to wiki, internal docs, Slack, etc.
    return digest

if __name__ == "__main__":
    print(generate_faq_digest())
```

## 7. Internal Documentation Generator

Auto-update internal docs with policy Q&A.

```bash
# gen_docs.py
from agent import answer_question

QUESTIONS_FOR_DOCS = {
    "leave": "What are the leave policies?",
    "remote": "Can I work remotely?",
    "equipment": "What equipment do I get?",
}

for section, question in QUESTIONS_FOR_DOCS.items():
    answer = answer_question(question)
    print(f"\n## {section.title()}\n{answer}")
```

## Environment Setup

For all integrations, set up your environment:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
MODEL=claude-sonnet-5-5

# For Slack:
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...

# For web:
FLASK_ENV=production
FLASK_APP=web_app.py
```

## Error Handling

All integrations should handle:

1. **API failures** (network errors, rate limits)
   ```python
   try:
       answer = answer_question(question)
   except anthropic.RateLimitError:
       return "Service busy, try again in a moment"
   except anthropic.APIError as e:
       return f"Service error: {e}"
   ```

2. **Out-of-scope questions**
   - Agent should decline, but check for phrases like "I don't know" or "outside HR scope"
   - If detected, offer to escalate to HR

3. **Slow responses**
   - Agent typically responds in <2 seconds
   - Set a timeout and fall back to "Let me escalate this to HR"

## Monitoring & Logging

Track:
- Questions asked (aggregated, no PII)
- Response times
- Error rates
- User satisfaction (thumbs up/down)

```python
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def answer_with_logging(question):
    start = datetime.now()
    try:
        answer = answer_question(question)
        elapsed = (datetime.now() - start).total_seconds()
        logger.info(f"QUESTION_ANSWERED topic={infer_topic(question)} time={elapsed}s")
        return answer
    except Exception as e:
        logger.error(f"QUESTION_FAILED error={e}")
        raise
```

## Security Considerations

1. **No PII in logs:** Don't log employee names, emails, or personal data
2. **Rate limiting:** Prevent abuse (e.g., 10 questions per minute per user)
3. **Access control:** If sensitive HR info is added, restrict access per role
4. **API key management:** Use environment variables or secrets manager, never hardcode
5. **Audit trail:** Log who asked what, when (for compliance)

## Performance Tips

1. **Pre-load policies:** Keep `policies` in memory (loaded on startup)
2. **Cache answers:** Store recent Q&A pairs in Redis if many duplicate questions
3. **Async calls:** Use async/await for non-blocking I/O in web integrations
4. **Batch API calls:** If scaling to 100+ questions/minute, batch calls to Anthropic API

---

**Next:** Start with Slack (low friction) or a simple web form, measure employee engagement, then expand to other channels.
