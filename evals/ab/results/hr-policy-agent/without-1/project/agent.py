#!/usr/bin/env python3
"""HR Policy Agent - Answers employee questions about company HR policies."""

import os
from pathlib import Path
import llm


def load_policies(policies_dir: str = "policies") -> str:
    """Load all HR policies from markdown files and return as a single context string."""
    policies_path = Path(policies_dir)
    if not policies_path.exists():
        raise FileNotFoundError(f"Policies directory not found: {policies_dir}")

    policies = []
    for md_file in sorted(policies_path.glob("*.md")):
        with open(md_file, "r") as f:
            content = f.read()
            policies.append(f"## {md_file.name}\n\n{content}\n")

    return "\n".join(policies)


def create_system_prompt(policies_context: str) -> str:
    """Create the system prompt for the HR policy agent."""
    return f"""You are a helpful HR policy assistant. Your role is to answer employee questions about company HR policies accurately and clearly.

When answering questions:
- Refer directly to the policy documentation provided
- Be specific and cite relevant policy sections
- If information is not covered in the policies, say so clearly
- If a question requires clarification, ask follow-up questions
- Be professional and empathetic in your responses

Here are the company's HR policies:

{policies_context}"""


def chat_with_agent(policies_context: str):
    """Run an interactive chat session with the HR policy agent."""
    system_prompt = create_system_prompt(policies_context)
    messages = []

    print("HR Policy Assistant")
    print("=" * 50)
    print("Ask me anything about company HR policies.")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except EOFError:
            # Handle EOF gracefully when input is piped
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("Thank you for using the HR Policy Assistant. Goodbye!")
            break

        # Add user message to conversation history
        messages.append({"role": "user", "content": user_input})

        # Get response from Claude
        response = llm.complete(
            system=system_prompt,
            messages=messages,
            max_tokens=1024
        )

        assistant_response = llm.text_of(response)

        # Add assistant response to conversation history
        messages.append({"role": "assistant", "content": assistant_response})

        print(f"\nAssistant: {assistant_response}\n")


def answer_question(question: str, policies_context: str) -> str:
    """Answer a single question without conversation history."""
    system_prompt = create_system_prompt(policies_context)
    messages = [{"role": "user", "content": question}]

    response = llm.complete(
        system=system_prompt,
        messages=messages,
        max_tokens=1024
    )

    return llm.text_of(response)


if __name__ == "__main__":
    import sys

    # Load all policies
    policies_context = load_policies()

    # If a question is provided as an argument, answer it directly
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        answer = answer_question(question, policies_context)
        print(answer)
    else:
        # Otherwise, start interactive chat
        chat_with_agent(policies_context)
