#!/usr/bin/env python3
"""
Test script for the HR Policy Agent.

Demonstrates the agent answering various policy questions without requiring
interactive input.
"""

from pathlib import Path
from anthropic import Anthropic

# Initialize the Anthropic client
client = Anthropic()


def load_policies(policies_dir: str = "policies") -> dict[str, str]:
    """Load all policy documents from the policies directory."""
    policies = {}
    policies_path = Path(policies_dir)

    for policy_file in sorted(policies_path.glob("*.md")):
        policy_name = policy_file.stem
        with open(policy_file, "r") as f:
            policies[policy_name] = f.read()

    return policies


def create_system_prompt(policies: dict[str, str]) -> str:
    """Create a system prompt that includes all HR policies."""
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


def test_agent():
    """Test the agent with a series of sample questions."""
    policies = load_policies()
    system_prompt = create_system_prompt(policies)

    # Sample questions to test
    test_questions = [
        "How much annual leave do full-time employees get per year?",
        "Can I work from overseas for a month?",
        "What's the process for booking a flight for business travel?",
        "Do I need a medical certificate for 2 days of sick leave?",
        "What's the home office allowance?",
        "Can I claim alcohol on my expenses?",
    ]

    print("=" * 70)
    print("HR POLICY AGENT - TEST RUN")
    print("=" * 70)
    print(f"\n✓ Loaded {len(policies)} policies\n")

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'─' * 70}")
        print(f"Question {i}: {question}")
        print("─" * 70)

        response = client.messages.create(
            model="claude-opus-5-5",
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": question}]
        )

        answer = response.content[0].text
        print(f"\nAnswer: {answer}")

    print(f"\n{'=' * 70}")
    print("Test completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    test_agent()
