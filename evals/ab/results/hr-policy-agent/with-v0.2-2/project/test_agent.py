#!/usr/bin/env python3
"""
Test script for the HR Policy Agent
Demonstrates the agent answering various HR policy questions.
"""

import os
from pathlib import Path
from anthropic import Anthropic

# Initialize the Anthropic client
client = Anthropic()


def load_policies():
    """Load all HR policies from the policies/ directory."""
    policies_dir = Path(__file__).parent / "policies"
    policies = {}

    for policy_file in sorted(policies_dir.glob("*.md")):
        with open(policy_file, "r") as f:
            policies[policy_file.stem] = f.read()

    return policies


def build_system_prompt(policies):
    """Build a system prompt that includes all HR policies."""
    policies_text = "\n\n".join(
        f"## {name.replace('_', ' ').title()}\n{content}"
        for name, content in policies.items()
    )

    return f"""You are an HR Policy Assistant for a company. Your job is to help employees understand and navigate the company's HR policies.

You have access to the following HR policies:

{policies_text}

Guidelines for your responses:
1. Answer questions based on the policies provided above.
2. Be clear and concise in your explanations.
3. If a policy is ambiguous or a question falls outside the policies, acknowledge the limitation and suggest contacting HR directly.
4. Always cite the specific policy when providing information.
5. If you don't know the answer based on the policies, say so explicitly.
6. Be helpful and empathetic - you're helping employees understand their benefits and obligations."""


def test_agent():
    """Test the agent with sample questions."""
    policies = load_policies()
    system_prompt = build_system_prompt(policies)

    test_questions = [
        "How many days of annual leave do I get?",
        "Can I work from home?",
        "What should I do if my laptop is stolen?",
        "What's the travel policy for international flights?",
        "How much can I claim for meals while travelling?",
        "How long is parental leave?",
    ]

    print("=" * 70)
    print("HR Policy Agent - Test Session")
    print("=" * 70)

    conversation_history = []

    for question in test_questions:
        print(f"\n{'Question:':<15} {question}")
        print("-" * 70)

        conversation_history.append({
            "role": "user",
            "content": question
        })

        response = client.messages.create(
            model="claude-opus-5-5",
            max_tokens=512,
            system=system_prompt,
            messages=conversation_history
        )

        answer = response.content[0].text
        conversation_history.append({
            "role": "assistant",
            "content": answer
        })

        print(f"{'Answer:':<15} {answer}\n")

    print("=" * 70)
    print("Test completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    test_agent()
