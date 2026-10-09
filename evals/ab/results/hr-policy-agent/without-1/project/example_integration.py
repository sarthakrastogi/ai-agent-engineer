#!/usr/bin/env python3
"""
Example integrations of the HR Policy Agent.

This file shows different ways to use the agent in other applications.
"""

import agent
import json


# ============================================================================
# Example 1: Use as a Library in Another Python Script
# ============================================================================

def example_library_usage():
    """Show how to use the agent as a library."""
    print("Example 1: Using Agent as a Library")
    print("=" * 50)

    # Load policies once
    policies = agent.load_policies()

    # Ask multiple questions programmatically
    questions = [
        "How much annual leave do I get?",
        "Can I work remotely?",
        "What's the laptop refresh policy?"
    ]

    for question in questions:
        answer = agent.answer_question(question, policies)
        print(f"Q: {question}")
        print(f"A: {answer[:150]}...\n")


# ============================================================================
# Example 2: Create a Simple REST API Wrapper
# ============================================================================

def example_rest_api():
    """Example of wrapping the agent in a Flask REST API."""
    code = '''
# Save this as hr_api.py and run with: flask run

from flask import Flask, request, jsonify
import agent

app = Flask(__name__)

# Load policies once at startup
policies = agent.load_policies()


@app.route("/api/ask", methods=["POST"])
def ask_question():
    """Ask a question about HR policies."""
    data = request.json
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question is required"}), 400

    try:
        answer = agent.answer_question(question, policies)
        return jsonify({"question": question, "answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(debug=True)
'''
    print("\nExample 2: REST API Wrapper")
    print("=" * 50)
    print("Create a REST API by adding this code to hr_api.py:")
    print(code)
    print("\nUsage:")
    print('  curl -X POST http://localhost:5000/api/ask \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"question": "How much annual leave do I get?"}\'\n')


# ============================================================================
# Example 3: Batch Processing
# ============================================================================

def example_batch_processing():
    """Process multiple questions from a file."""
    code = '''
import agent
import json

# Load policies once
policies = agent.load_policies()

# Read questions from a JSON file
with open("questions.json", "r") as f:
    questions_data = json.load(f)

# Process each question
results = []
for item in questions_data:
    question = item["question"]
    employee_id = item.get("employee_id")

    answer = agent.answer_question(question, policies)
    results.append({
        "employee_id": employee_id,
        "question": question,
        "answer": answer,
        "timestamp": datetime.now().isoformat()
    })

# Save results
with open("answers.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Processed {len(results)} questions")
'''
    print("\nExample 3: Batch Processing")
    print("=" * 50)
    print("Process multiple questions from a file:")
    print(code)


# ============================================================================
# Example 4: Chat Session Export
# ============================================================================

def example_chat_export():
    """Show how to export and analyze conversations."""
    code = '''
import agent
import json
from datetime import datetime

def interactive_chat_with_export():
    """Run chat and save conversation to file."""
    policies = agent.load_policies()
    system_prompt = agent.create_system_prompt(policies)
    messages = []
    conversation = []

    session_id = datetime.now().isoformat()

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break

        # Add to message history
        messages.append({"role": "user", "content": user_input})

        # Get response
        response = agent.llm.complete(
            system=system_prompt,
            messages=messages,
            max_tokens=1024
        )
        answer = agent.llm.text_of(response)

        # Add to message history
        messages.append({"role": "assistant", "content": answer})

        # Store in conversation log
        conversation.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "assistant": answer
        })

        print(f"Assistant: {answer}\\n")

    # Save conversation
    with open(f"conversation_{session_id}.json", "w") as f:
        json.dump(conversation, f, indent=2)

    print(f"Conversation saved to conversation_{session_id}.json")

interactive_chat_with_export()
'''
    print("\nExample 4: Chat Session Export")
    print("=" * 50)
    print("Save conversations to JSON files:")
    print(code)


# ============================================================================
# Example 5: Integration with Slack
# ============================================================================

def example_slack_integration():
    """Show how to integrate with Slack."""
    code = '''
# Save as slack_bot.py
# Install: pip install slack-bolt python-dotenv

from slack_bolt import App
import agent

app = App(token="xoxb-...", signing_secret="...")

# Load policies once
policies = agent.load_policies()


@app.message(".*")
def handle_message(message, say):
    """Handle any message in the channel."""
    question = message["text"].strip()

    if question.lower() in ("help", "?"):
        say("Ask me anything about HR policies!")
        return

    try:
        answer = agent.answer_question(question, policies)
        say(f"*Q:* {question}\\n*A:* {answer}")
    except Exception as e:
        say(f"Error: {e}")


if __name__ == "__main__":
    app.start(port=3000)
'''
    print("\nExample 5: Slack Bot Integration")
    print("=" * 50)
    print("Create a Slack bot that answers policy questions:")
    print(code)


# ============================================================================
# Example 6: Monitoring and Logging
# ============================================================================

def example_monitoring():
    """Show how to add monitoring and logging."""
    code = '''
import agent
import logging
import time
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load policies once
policies = agent.load_policies()


def log_request(func):
    """Decorator to log agent requests."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        request_id = id(args) if args else "unknown"

        try:
            logger.info(f"Request {request_id} started")
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"Request {request_id} completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            logger.error(f"Request {request_id} failed: {e}")
            raise

    return wrapper


@log_request
def answer_with_monitoring(question):
    """Answer a question with monitoring."""
    return agent.answer_question(question, policies)


# Usage
answer = answer_with_monitoring("How much leave do I get?")
'''
    print("\nExample 6: Monitoring and Logging")
    print("=" * 50)
    print("Add logging and performance monitoring:")
    print(code)


# ============================================================================
# Example 7: Quality Testing
# ============================================================================

def example_quality_testing():
    """Show how to test answer quality."""
    code = '''
import agent

# Load policies
policies = agent.load_policies()

# Test cases with expected keywords
test_cases = [
    {
        "question": "How much annual leave do I get?",
        "expected_keywords": ["20 days", "annual leave"]
    },
    {
        "question": "Can I work from overseas?",
        "expected_keywords": ["2 weeks", "approval"]
    },
    {
        "question": "What about sick leave?",
        "expected_keywords": ["10 days", "medical certificate"]
    }
]

# Run tests
print("Quality Testing")
print("=" * 50)
passed = 0

for test in test_cases:
    answer = agent.answer_question(test["question"], policies)
    has_keywords = all(kw.lower() in answer.lower()
                       for kw in test["expected_keywords"])

    if has_keywords:
        print(f"✓ {test['question']}")
        passed += 1
    else:
        print(f"✗ {test['question']}")
        print(f"  Expected keywords: {test['expected_keywords']}")
        print(f"  Got: {answer[:100]}...")

print(f"\\nPassed: {passed}/{len(test_cases)}")
'''
    print("\nExample 7: Quality Testing")
    print("=" * 50)
    print("Test answer quality with keyword matching:")
    print(code)


if __name__ == "__main__":
    # Show all examples
    example_library_usage()
    example_rest_api()
    example_batch_processing()
    example_chat_export()
    example_slack_integration()
    example_monitoring()
    example_quality_testing()

    print("\n" + "=" * 50)
    print("See the code above for how to integrate the agent")
    print("into different applications and workflows.")
