#!/usr/bin/env python3
"""Interactive example of the HR policy agent.

Run with: python3 example.py
"""
from agent import answer_question


EXAMPLE_QUESTIONS = [
    "How much annual leave do full-time employees get?",
    "Can I work from home? How many days per week?",
    "Who needs to approve my international flight?",
    "What's my meal allowance while travelling?",
    "How often do I get a new laptop?",
]


def main():
    print("=" * 70)
    print("HR POLICY AGENT - Example Questions")
    print("=" * 70)
    print()

    for i, question in enumerate(EXAMPLE_QUESTIONS, 1):
        print(f"Question {i}: {question}")
        print("-" * 70)
        answer = answer_question(question)
        print(answer)
        print()
        print()


if __name__ == "__main__":
    main()
