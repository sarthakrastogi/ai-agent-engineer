#!/usr/bin/env python3
"""
HR Policy Agent - Answers employee questions about company HR policies.

This agent loads HR policies from markdown files and uses Claude to answer
questions about them in a helpful, conversational manner.
"""

import os
from pathlib import Path
import anthropic


def load_policies(policies_dir: str = "policies") -> str:
    """Load all HR policy markdown files and combine them into a single context."""
    policies_content = []
    policies_path = Path(policies_dir)

    if not policies_path.exists():
        return "No policies directory found."

    # Load all .md files from the policies directory
    for policy_file in sorted(policies_path.glob("*.md")):
        try:
            with open(policy_file, "r") as f:
                content = f.read()
                policies_content.append(f"## File: {policy_file.name}\n{content}")
        except Exception as e:
            print(f"Warning: Could not load {policy_file}: {e}")

    return "\n\n".join(policies_content)


def create_system_prompt(policies: str) -> str:
    """Create the system prompt with the HR policies embedded."""
    return f"""You are a helpful HR policy assistant. Your role is to answer employee questions
about company HR policies in a friendly and clear manner.

Here are the company HR policies:

{policies}

When answering questions:
1. Refer to the specific policies provided above
2. Be clear and concise
3. If a question isn't covered by the policies, say so politely
4. For ambiguous questions, ask for clarification
5. Always be friendly and professional"""


def run_hr_agent():
    """Run the interactive HR policy agent."""
    # Initialize the Anthropic client
    client = anthropic.Anthropic()

    # Load policies
    print("Loading HR policies...")
    policies = load_policies()

    if not policies or policies == "No policies directory found.":
        print("Error: Could not load policies. Make sure the 'policies' directory exists.")
        return

    system_prompt = create_system_prompt(policies)

    print("\n" + "=" * 60)
    print("Welcome to the HR Policy Agent!")
    print("Ask questions about company HR policies.")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("=" * 60 + "\n")

    conversation_history = []

    while True:
        # Get user input
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            print("\nThank you for using the HR Policy Agent. Goodbye!")
            break

        # Add user message to history
        conversation_history.append({"role": "user", "content": user_input})

        # Get response from Claude
        try:
            response = client.messages.create(
                model="claude-opus-5-5",
                max_tokens=1024,
                system=system_prompt,
                messages=conversation_history,
            )

            assistant_message = response.content[0].text

            # Add assistant response to history
            conversation_history.append(
                {"role": "assistant", "content": assistant_message}
            )

            print(f"\nAgent: {assistant_message}\n")

        except anthropic.APIError as e:
            print(f"\nError communicating with API: {e}\n")
            # Remove the user message if there was an error
            conversation_history.pop()


def main():
    """Main entry point."""
    run_hr_agent()


if __name__ == "__main__":
    main()
