"""HR policy agent. Answers employee questions about company policies."""
import os
from pathlib import Path

from llm import complete, text_of


def load_policies(policies_dir: str = "policies") -> str:
    """Load all markdown policy files and concatenate into context."""
    policies_path = Path(policies_dir)
    policies = []

    for policy_file in sorted(policies_path.glob("*.md")):
        with open(policy_file, "r") as f:
            policies.append(f.read())

    return "\n\n---\n\n".join(policies)


def build_system_prompt(policies_text: str) -> str:
    """Build the system prompt with embedded policies."""
    return f"""You are an HR policy assistant for company employees.
Your job is to answer questions about company HR policies accurately and helpfully.

You have access to the following company policies:

{policies_text}

Guidelines:
- Answer questions directly based on the policies provided.
- Always cite the relevant policy section when giving an answer.
- If a question is not covered by the policies, say so explicitly.
- Be conversational but professional.
- Do not make up or invent policies that are not in the provided text.
- If someone asks about a policy you're unsure about, suggest they contact HR.
"""


def answer_question(question: str, policies_dir: str = "policies") -> str:
    """Answer an employee's HR policy question."""
    policies_text = load_policies(policies_dir)
    system_prompt = build_system_prompt(policies_text)

    messages = [{"role": "user", "content": question}]

    response = complete(
        system=system_prompt,
        messages=messages,
        max_tokens=1024,
    )

    return text_of(response)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = input("Ask a question about HR policies: ")

    answer = answer_question(question)
    print(answer)
