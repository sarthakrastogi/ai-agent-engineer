#!/usr/bin/env python3
"""
Test script for the HR Policy Agent.

Tests basic functionality with typical employee questions.
"""

from hr_agent import load_policies, answer_question


def test_hr_agent():
    """Run a series of test questions through the agent."""
    print("Loading policies...\n")
    policies = load_policies()

    test_questions = [
        "How many days of annual leave do I get as a full-time employee?",
        "What's the process for meal expenses when I travel for work?",
        "Can I work from home? If so, how many days per week?",
        "What happens if I want to work from overseas for a month?",
        "How often can I get a new laptop?",
        "What is the parental leave policy?",
        "Do you cover pet insurance?",  # Not in policies
    ]

    conversation_history = []

    for question in test_questions:
        print(f"Q: {question}")
        answer, conversation_history = answer_question(
            question, policies, conversation_history
        )
        print(f"A: {answer}\n")
        print("-" * 60 + "\n")


if __name__ == "__main__":
    test_hr_agent()
