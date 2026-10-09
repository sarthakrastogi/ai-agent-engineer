#!/usr/bin/env python3
"""
HR Policy Agent

A simple agent that answers employee questions about HR policies using Claude.
Loads policies from the policies/ directory and uses them to provide accurate,
policy-backed answers to employee inquiries.
"""

import os
import sys
from pathlib import Path
from anthropic import Anthropic

# Initialize the Anthropic client
client = Anthropic()


def load_policies(policies_dir: str = "policies") -> dict[str, str]:
    """
    Load all policy documents from the policies directory.

    Returns:
        A dictionary mapping policy names to their content.
    """
    policies = {}
    policies_path = Path(policies_dir)

    if not policies_path.exists():
        print(f"Error: Policies directory '{policies_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    for policy_file in sorted(policies_path.glob("*.md")):
        policy_name = policy_file.stem
        try:
            with open(policy_file, "r") as f:
                policies[policy_name] = f.read()
        except Exception as e:
            print(f"Warning: Could not read {policy_file}: {e}", file=sys.stderr)

    return policies


def create_system_prompt(policies: dict[str, str]) -> str:
    """
    Create a system prompt that includes all HR policies.

    Returns:
        The system prompt for the Claude model.
    """
    policy_text = "\n\n---\n\n".join(
        f"## {name.replace('_', ' ').title()} Policy\n{content}"
        for name, content in policies.items()
    )

    return f"""You are an HR Policy Assistant helping employees understand company policies.

You have access to the following company policies:

{policy_text}

When answering employee questions:
1. Base your answers strictly on the policies provided above.
2. If a question is not covered by the policies, clearly state that you don't have that information and suggest they contact HR.
3. Be helpful and professional in your tone.
4. If the question is ambiguous, ask for clarification.
5. Always cite the relevant policy section when providing an answer.
"""


def run_agent(policies_dir: str = "policies"):
    """
    Run the HR Policy Agent in an interactive conversation loop.
    """
    policies = load_policies(policies_dir)

    if not policies:
        print("Error: No policy files found.", file=sys.stderr)
        sys.exit(1)

    print(f"✓ Loaded {len(policies)} policies: {', '.join(policies.keys())}")
    print("\nHR Policy Agent Ready!")
    print("Ask any questions about HR policies. Type 'exit' or 'quit' to stop.\n")
    print("-" * 60)

    system_prompt = create_system_prompt(policies)
    conversation_history = []

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                print("\nThank you for using the HR Policy Agent. Goodbye!")
                break

            # Add user message to conversation history
            conversation_history.append({
                "role": "user",
                "content": user_input
            })

            # Get response from Claude
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

            print(f"\nAgent: {assistant_message}")

        except KeyboardInterrupt:
            print("\n\nAgent stopped by user. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    run_agent()
