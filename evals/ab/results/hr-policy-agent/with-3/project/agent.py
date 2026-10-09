#!/usr/bin/env python3
"""
HR Policy Agent: Answers employee questions about company HR policies.

This agent uses retrieval-augmented generation to search relevant policies
and provide accurate, cited answers. It's designed to be small and practical:
- All policies fit in context (~2k tokens), so we use simple string matching
  for retrieval before passing to the LLM.
- The agent refuses questions outside its scope (not HR policy related).
- All answers are grounded in the policy text with citations.
"""

import os
import pathlib
from dataclasses import dataclass

from llm import complete, text_of


POLICIES_DIR = pathlib.Path(__file__).parent / "policies"


@dataclass
class RetrievalResult:
    """A retrieved policy chunk with metadata."""
    filename: str
    title: str
    content: str

    def __str__(self) -> str:
        return f"**{self.title}** ({self.filename}):\n{self.content}"


def load_policies() -> dict[str, str]:
    """Load all policy files from policies/ directory.

    Returns:
        Dict mapping filename to full content (title + body).
    """
    policies = {}
    for policy_file in sorted(POLICIES_DIR.glob("*.md")):
        policies[policy_file.name] = policy_file.read_text()
    return policies


def retrieve_relevant_policies(question: str, policies: dict[str, str], top_k: int = 3) -> list[RetrievalResult]:
    """Retrieve the most relevant policies for a question using simple keyword matching.

    This uses a simple TF-IDF-like scoring: count word overlaps between the question
    and policy text, weighted by policy section headers.

    Args:
        question: The employee's question.
        policies: Dict of all loaded policies.
        top_k: How many policies to return (max 3 to keep context tight).

    Returns:
        List of RetrievalResult objects, ranked by relevance.
    """
    question_words = set(question.lower().split())

    scores = []
    for filename, content in policies.items():
        # Simple scoring: word overlap
        content_words = set(content.lower().split())
        overlap = len(question_words & content_words)

        # Boost score if question words appear in headers (markdown #)
        lines = content.split('\n')
        header_boost = sum(
            len(set(line.replace('#', '').lower().split()) & question_words)
            for line in lines if line.startswith('#')
        )

        total_score = overlap + (header_boost * 2)  # Weight headers more

        if total_score > 0:
            # Extract title from first markdown header
            title = next(
                (line.replace('#', '').strip() for line in lines if line.startswith('#')),
                filename.replace('.md', '').replace('-', ' ').title()
            )
            scores.append((total_score, filename, title, content))

    # Sort by score descending and take top_k
    scores.sort(reverse=True)
    results = [
        RetrievalResult(filename=fn, title=title, content=content)
        for _, fn, title, content in scores[:top_k]
    ]
    return results


def build_system_prompt(retrieved_policies: list[RetrievalResult]) -> str:
    """Build the system prompt with retrieved policy context.

    Args:
        retrieved_policies: List of relevant RetrievalResult objects.

    Returns:
        System prompt string.
    """
    context = "\n\n".join(str(result) for result in retrieved_policies) if retrieved_policies else ""

    return f"""You are an HR policy assistant helping employees understand company policies.

Your role:
- Answer questions about HR policies accurately and clearly.
- Always cite which policy document your answer comes from.
- If a question is not about HR policies, politely decline to answer and suggest contacting HR.
- If you don't find the answer in the provided policies, say so and recommend contacting HR.
- Be concise and helpful—employees often just need a quick clarification.

Retrieved relevant policies:
{context}

Guidelines for your answer:
1. Quote or closely paraphrase the relevant policy text.
2. Mention the policy document name in parentheses, e.g., "(from Leave policy)".
3. If the policy is ambiguous, say so and recommend contacting HR for clarification.
4. Do not make up or infer policies beyond what's stated.
"""


def answer_question(question: str, policies: dict[str, str] | None = None) -> str:
    """Answer an HR policy question.

    Args:
        question: The employee's question.
        policies: Pre-loaded policies dict. If None, loads from disk.

    Returns:
        The agent's answer.
    """
    if policies is None:
        policies = load_policies()

    # Retrieve relevant policies
    retrieved = retrieve_relevant_policies(question, policies, top_k=3)

    # Build system prompt with context
    system_prompt = build_system_prompt(retrieved)

    # Call the LLM
    response = complete(
        system=system_prompt,
        messages=[{"role": "user", "content": question}],
        max_tokens=512
    )

    return text_of(response)


def main():
    """Interactive REPL for asking HR policy questions."""
    policies = load_policies()
    print("HR Policy Assistant")
    print("=" * 50)
    print("Ask questions about company HR policies. Type 'quit' to exit.\n")

    while True:
        try:
            question = input("Q: ").strip()
            if question.lower() == "quit":
                break
            if not question:
                continue

            print(f"\nRetrieving policies...")
            answer = answer_question(question, policies)
            print(f"A: {answer}\n")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
