#!/usr/bin/env python3
"""
Example usage of the HR Policy Agent as a library.

Shows how to integrate the agent into other applications.
"""

from pathlib import Path
from anthropic import Anthropic

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


class HRPolicyAgent:
    """A simple HR Policy Agent that can be used programmatically."""

    def __init__(self, policies_dir: str = "policies"):
        """Initialize the agent with policies from the specified directory."""
        self.policies = load_policies(policies_dir)
        self.system_prompt = create_system_prompt(self.policies)
        self.conversation_history = []

    def ask(self, question: str) -> str:
        """
        Ask a question and get a response from the HR Policy Agent.

        Args:
            question: The employee's question about HR policies

        Returns:
            The agent's policy-backed response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": question
        })

        # Get response from Claude
        response = client.messages.create(
            model="claude-opus-5-5",
            max_tokens=1024,
            system=self.system_prompt,
            messages=self.conversation_history
        )

        assistant_message = response.content[0].text

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def reset_conversation(self):
        """Reset the conversation history for a new conversation."""
        self.conversation_history = []


# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = HRPolicyAgent()

    # Ask some questions
    print("=== HR Policy Agent Example ===\n")

    # Single question
    question1 = "What's the home office allowance?"
    print(f"Q: {question1}")
    answer1 = agent.ask(question1)
    print(f"A: {answer1}\n")

    # Follow-up question (maintains context)
    question2 = "Can I claim it for remote work?"
    print(f"Q: {question2}")
    answer2 = agent.ask(question2)
    print(f"A: {answer2}\n")

    # Another follow-up
    question3 = "How often can I get it?"
    print(f"Q: {question3}")
    answer3 = agent.ask(question3)
    print(f"A: {answer3}\n")

    # Reset for a new conversation
    agent.reset_conversation()

    # New conversation
    print("=== New Conversation ===\n")
    question4 = "What's the sick leave policy?"
    print(f"Q: {question4}")
    answer4 = agent.ask(question4)
    print(f"A: {answer4}\n")
