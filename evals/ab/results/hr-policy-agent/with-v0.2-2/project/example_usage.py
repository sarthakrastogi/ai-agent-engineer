#!/usr/bin/env python3
"""
Example usage of the HR Policy Agent
Demonstrates how to use the agent programmatically.
"""

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


def query_agent(question: str, conversation_history: list) -> tuple[str, list]:
    """
    Query the HR Policy Agent.

    Args:
        question: The question to ask
        conversation_history: List of previous messages in the conversation

    Returns:
        A tuple of (response, updated_conversation_history)
    """
    policies = load_policies()
    system_prompt = build_system_prompt(policies)

    conversation_history.append({
        "role": "user",
        "content": question
    })

    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=1024,
        system=system_prompt,
        messages=conversation_history
    )

    assistant_message = response.content[0].text
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })

    return assistant_message, conversation_history


def example_1_single_question():
    """Example 1: Ask a single question."""
    print("\n" + "=" * 70)
    print("Example 1: Single Question")
    print("=" * 70)

    question = "How many days of annual leave do full-time employees get?"
    response, _ = query_agent(question, [])

    print(f"\nQuestion: {question}")
    print(f"\nAnswer: {response}")


def example_2_multi_turn():
    """Example 2: Multi-turn conversation."""
    print("\n" + "=" * 70)
    print("Example 2: Multi-Turn Conversation")
    print("=" * 70)

    history = []

    questions = [
        "What's the remote work policy?",
        "How often can I get a home office allowance?",
        "Can I work overseas?"
    ]

    for question in questions:
        response, history = query_agent(question, history)
        print(f"\nQ: {question}")
        print(f"A: {response}")


def example_3_specific_scenarios():
    """Example 3: Complex scenario questions."""
    print("\n" + "=" * 70)
    print("Example 3: Scenario-Based Questions")
    print("=" * 70)

    history = []

    scenarios = [
        "I'm planning to travel to Australia for 2 weeks for a client meeting. What do I need to do?",
        "Can I claim meals during this trip and how much?",
        "What if I want to extend by 1 week and work remotely from there?"
    ]

    for scenario in scenarios:
        response, history = query_agent(scenario, history)
        print(f"\nScenario: {scenario}")
        print(f"Response: {response}")


def example_4_edge_cases():
    """Example 4: Handling edge cases and out-of-scope questions."""
    print("\n" + "=" * 70)
    print("Example 4: Edge Cases and Out-of-Scope Questions")
    print("=" * 70)

    history = []

    edge_questions = [
        "What's the salary review process?",
        "I need parental leave - what are my eligibility requirements?",
        "My equipment was stolen. What should I do immediately?"
    ]

    for question in edge_questions:
        response, history = query_agent(question, history)
        print(f"\nQ: {question}")
        print(f"A: {response}")


if __name__ == "__main__":
    print("\nHR Policy Agent - Usage Examples")
    print("These examples demonstrate different ways to use the agent.")

    try:
        example_1_single_question()
        example_2_multi_turn()
        example_3_specific_scenarios()
        example_4_edge_cases()

        print("\n" + "=" * 70)
        print("All examples completed successfully!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure ANTHROPIC_API_KEY is set in your environment.")
