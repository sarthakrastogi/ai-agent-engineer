#!/usr/bin/env python3
"""
Demo script: Run the HR policy agent on predefined questions.
"""

import agent


def run_demo():
    """Run the agent on several example questions."""
    policies = agent.load_policies()

    questions = [
        "How many days of annual leave do I get?",
        "Can I work from home? How many days?",
        "What happens if I get sick and need to take leave?",
        "When can I get a new laptop?",
        "I want to work remotely for a month from overseas, is that allowed?",
    ]

    print("🤖 HR Policy Agent Demo")
    print("=" * 60)
    print()

    for i, question in enumerate(questions, 1):
        print(f"Question {i}: {question}")
        print("-" * 60)

        answer = agent.run_agent_loop(question, policies)
        print(f"Answer: {answer}")
        print()


if __name__ == "__main__":
    run_demo()
