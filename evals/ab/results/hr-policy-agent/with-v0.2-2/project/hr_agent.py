#!/usr/bin/env python3
"""
HR Policy Agent
A simple agent that answers employee questions about HR policies using Claude.
"""

import os
import sys
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


def main():
    """Main conversation loop for the HR Policy Agent."""
    print("=" * 60)
    print("HR Policy Agent")
    print("=" * 60)
    print("\nWelcome! I'm here to help you understand company HR policies.")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    # Load policies
    policies = load_policies()
    if not policies:
        print("Error: No HR policies found in policies/ directory")
        sys.exit(1)

    system_prompt = build_system_prompt(policies)

    # Conversation history for multi-turn dialogue
    conversation_history = []

    while True:
        # Get user input
        try:
            user_input = input("\nYou: ").strip()
        except EOFError:
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            print("\nThank you for using the HR Policy Agent. Goodbye!")
            break

        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # Get response from Claude
        try:
            response = client.messages.create(
                model="claude-opus-5-5",
                max_tokens=1024,
                system=system_prompt,
                messages=conversation_history
            )

            assistant_message = response.content[0].text

            # Add assistant response to history
            conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            print(f"\nAssistant: {assistant_message}")

        except Exception as e:
            print(f"\nError: {e}")
            # Remove the user message from history if there was an error
            conversation_history.pop()


if __name__ == "__main__":
    main()
