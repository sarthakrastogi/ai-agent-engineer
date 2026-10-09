#!/usr/bin/env python3
"""
HR Policy Agent - Demo version (no API key required)

This demo shows how the agent searches and answers policy questions
without making actual API calls. It simulates intelligent policy matching.
"""

import sys
from pathlib import Path
from typing import List, Tuple

def load_policies():
    """Load all policy files from the policies directory."""
    policies = {}
    policies_dir = Path(__file__).parent / "policies"

    for policy_file in policies_dir.glob("*.md"):
        with open(policy_file, 'r') as f:
            policies[policy_file.stem] = f.read()

    return policies

def search_policies(query: str, policies: dict) -> List[Tuple[str, str]]:
    """Search policies and return matching content with relevance."""
    query_lower = query.lower()
    results = []

    # Define keyword mappings for better search relevance
    keyword_mapping = {
        "leave": ["leave", "vacation", "days off", "holiday", "parental", "sick"],
        "expenses": ["expense", "claim", "meal", "receipt", "approval", "reimburs"],
        "remote-work": ["remote", "work from home", "home office", "overseas", "home", "working"],
        "travel": ["travel", "flight", "booking", "hotel", "transport"],
        "equipment": ["equipment", "laptop", "device", "phone", "stolen", "lost"],
    }

    # Score each policy
    for policy_name, content in policies.items():
        score = 0

        # Direct name match
        if query_lower in policy_name.lower():
            score += 10

        # Content match
        if query_lower in content.lower():
            score += 5

        # Keyword-based match
        for policy_key, keywords in keyword_mapping.items():
            if policy_name == policy_key:
                for keyword in keywords:
                    if keyword in query_lower:
                        score += 3

        # Also match keywords in content
        for policy_key, keywords in keyword_mapping.items():
            for keyword in keywords:
                if keyword in query_lower and keyword in content.lower():
                    score += 2

        if score > 0:
            results.append((policy_name, content, score))

    # Sort by score (highest first)
    results.sort(key=lambda x: x[2], reverse=True)
    return [(name, content) for name, content, _ in results]

def get_relevant_answer(query: str, policies: dict) -> str:
    """Generate an answer based on policy search results."""
    results = search_policies(query, policies)

    if not results:
        return """I couldn't find relevant policy information for that question.
Please contact the HR department for clarification:
- Email: hr@company.com
- Internal chat: #hr-support"""

    # Build response from most relevant policies
    response_parts = []

    for policy_name, content in results:
        display_name = policy_name.replace("-", " ").title()
        response_parts.append(f"**From {display_name} policy:**\n{content}")

    base_response = "\n\n".join(response_parts)

    # Add contextual note
    if len(results) > 0:
        response = f"{base_response}\n\n---\n\nIf you have any further questions, please reach out to HR."
    else:
        response = base_response

    return response

def run_demo(user_question: str):
    """Run the HR policy agent demo."""
    print(f"\n{'='*70}")
    print(f"Employee: {user_question}")
    print('='*70)

    policies = load_policies()
    answer = get_relevant_answer(user_question, policies)

    print(f"\nAssistant: {answer}")

def main():
    """Main entry point."""
    print("🚀 HR Policy Agent - Demo Mode")
    print("="*70)
    print("This demo simulates the HR policy agent without API credentials.\n")

    # Example questions to demonstrate the agent
    example_questions = [
        "How much annual leave do I get?",
        "Can I work remotely?",
        "What's the policy on meal expenses while traveling?",
        "When can I get a new laptop?",
        "What if I need parental leave?",
        "How do I claim expenses?",
        "What's the travel booking process?",
    ]

    if len(sys.argv) > 1:
        # Use question from command line
        user_question = " ".join(sys.argv[1:])
        run_demo(user_question)
    else:
        # Run example questions
        for question in example_questions:
            run_demo(question)

if __name__ == "__main__":
    main()
