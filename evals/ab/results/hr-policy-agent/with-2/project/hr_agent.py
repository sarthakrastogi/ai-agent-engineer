#!/usr/bin/env python3
"""
HR Policy Agent: Answers employee questions about company HR policies.

Design:
- Single LLM call + prompt caching (policies ~3KB fit in context)
- No loops needed: policies are deterministic reference material
- Cites which policy document each answer comes from
- Uses Claude with prompt caching for efficient repeated queries
"""

import os
import sys
from pathlib import Path
from typing import Optional

from anthropic import Anthropic

# Initialize the Anthropic client
client = Anthropic()


def load_policies(policies_dir: str = "policies") -> dict[str, str]:
    """Load all HR policy files from the policies directory."""
    policies = {}
    policies_path = Path(policies_dir)

    if not policies_path.exists():
        raise FileNotFoundError(f"Policies directory not found: {policies_dir}")

    for policy_file in sorted(policies_path.glob("*.md")):
        policy_name = policy_file.stem
        with open(policy_file, "r") as f:
            policies[policy_name] = f.read()

    if not policies:
        raise FileNotFoundError(f"No policy files found in {policies_dir}")

    return policies


def format_policies_for_context(policies: dict[str, str]) -> str:
    """Format policies into a single string for the LLM context."""
    formatted = "# HR POLICIES\n\n"
    for policy_name, content in policies.items():
        formatted += f"## Policy: {policy_name.upper()}\n"
        formatted += content
        formatted += "\n\n"
    return formatted


def create_system_prompt(policies_context: str) -> str:
    """Create the system prompt with embedded policies."""
    return f"""You are an HR Policy Assistant. Your role is to answer employee questions about company HR policies accurately and helpfully.

IMPORTANT INSTRUCTIONS:
1. Base all answers ONLY on the policies provided below. Do not make up policies or guess.
2. Always cite which policy document(s) your answer comes from.
3. If a question is not covered by the policies, say so clearly: "This is not covered in the current HR policies. Please contact HR directly."
4. Be friendly and professional in tone.
5. If an employee's situation is complex or needs approval, suggest they contact HR for guidance.

{policies_context}"""


def answer_question(
    question: str,
    policies: dict[str, str],
    conversation_history: Optional[list] = None,
) -> tuple[str, list]:
    """
    Answer an employee's HR policy question using Claude with prompt caching.

    Args:
        question: The employee's question
        policies: Dictionary of policy documents
        conversation_history: Optional list of previous messages for multi-turn

    Returns:
        Tuple of (answer, updated_conversation_history)
    """
    if conversation_history is None:
        conversation_history = []

    policies_context = format_policies_for_context(policies)
    system_prompt = create_system_prompt(policies_context)

    # Add the new question to conversation history
    conversation_history.append({"role": "user", "content": question})

    # Make the API call with prompt caching
    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=conversation_history,
    )

    # Extract the assistant's response
    assistant_message = response.content[0].text

    # Add to conversation history
    conversation_history.append({"role": "assistant", "content": assistant_message})

    # Print cache usage stats
    usage = response.usage
    cache_creation = getattr(usage, "cache_creation_input_tokens", 0)
    cache_read = getattr(usage, "cache_read_input_tokens", 0)

    if cache_creation > 0 or cache_read > 0:
        print(f"\n[Cache stats: created={cache_creation}, read={cache_read}]")

    return assistant_message, conversation_history


def interactive_mode(policies: dict[str, str]) -> None:
    """Run the agent in interactive mode for multi-turn conversation."""
    print("\n" + "=" * 60)
    print("HR POLICY ASSISTANT")
    print("=" * 60)
    print("Ask me about any HR policies. Type 'exit' or 'quit' to end.\n")

    conversation_history = []

    while True:
        try:
            question = input("Your question: ").strip()
        except EOFError:
            break

        if question.lower() in ("exit", "quit"):
            print("Thank you for using the HR Policy Assistant. Goodbye!")
            break

        if not question:
            print("Please enter a question.\n")
            continue

        print("\nAssistant: ", end="")
        answer, conversation_history = answer_question(
            question, policies, conversation_history
        )
        print(answer)
        print()


def main():
    """Main entry point."""
    # Load policies
    try:
        policies = load_policies()
        print(f"✓ Loaded {len(policies)} policy documents")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # If a question is provided as command-line argument, answer it and exit
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        print(f"\nQuestion: {question}\n")
        answer, _ = answer_question(question, policies)
        print(f"Answer:\n{answer}")
    else:
        # Otherwise, run interactive mode
        interactive_mode(policies)


if __name__ == "__main__":
    main()
