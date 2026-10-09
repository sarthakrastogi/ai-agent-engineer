#!/usr/bin/env python3
"""
Example usage of the HR policy agent.

This script demonstrates how to use the agent programmatically and shows
what kinds of questions it handles well.
"""

from agent import answer_question


EXAMPLE_QUESTIONS = [
    # Leave questions
    "How many days of annual leave do I get per year?",
    "Can I carry over unused leave to next year?",
    "What's the policy for parental leave?",

    # Remote work
    "Can I work from home? How many days per week?",
    "What if I want to work remotely from overseas?",
    "Is there a home office allowance?",

    # Equipment
    "When do I get a new laptop?",
    "What should I do if my laptop is stolen?",

    # Expenses
    "What's the meal allowance when I'm travelling for work?",
    "Do I need approval to claim meal expenses?",
    "Can I claim alcohol expenses?",

    # Travel
    "Who needs to approve my flight?",
    "What class should I book flights in?",

    # Out of scope (should be declined)
    "What's the capital of France?",
    "When should I ask for a raise?",
]


def main():
    """Run example questions through the agent."""
    print("=" * 70)
    print("HR Policy Agent - Examples")
    print("=" * 70)

    for i, question in enumerate(EXAMPLE_QUESTIONS, 1):
        print(f"\n[Q{i}] {question}")
        print("-" * 70)
        try:
            answer = answer_question(question)
            print(answer)
        except Exception as e:
            print(f"Error: {e}")

        print()

    print("=" * 70)
    print("Examples complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
