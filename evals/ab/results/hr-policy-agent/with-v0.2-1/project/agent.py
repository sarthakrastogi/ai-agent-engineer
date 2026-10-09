#!/usr/bin/env python3
"""
HR Policy Agent: Answers employee questions about company HR policies.

Loads policies from the policies/ directory and uses Claude to answer questions
with policy-grounded responses.
"""

import json
import os
from pathlib import Path
import llm


# Load all policies from the policies directory
def load_policies() -> dict[str, str]:
    """Load all HR policies from policies/ directory."""
    policies = {}
    policies_dir = Path(__file__).parent / "policies"

    for policy_file in sorted(policies_dir.glob("*.md")):
        policy_name = policy_file.stem
        policies[policy_name] = policy_file.read_text()

    return policies


def build_policy_lookup_tool(policies: dict[str, str]) -> dict:
    """Build the policy lookup tool definition for Claude."""
    policy_names = list(policies.keys())

    return {
        "name": "lookup_policy",
        "description": "Look up a specific HR policy by name to get its full details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_name": {
                    "type": "string",
                    "enum": policy_names,
                    "description": f"The policy to look up. One of: {', '.join(policy_names)}"
                }
            },
            "required": ["policy_name"]
        }
    }


def lookup_policy(policy_name: str, policies: dict[str, str]) -> str:
    """Look up a policy and return its content."""
    if policy_name not in policies:
        return f"Policy '{policy_name}' not found. Available policies: {', '.join(policies.keys())}"
    return policies[policy_name]


def run_agent_loop(question: str, policies: dict[str, str]) -> str:
    """Run the agent loop to answer a question about HR policies."""
    tools = [build_policy_lookup_tool(policies)]

    system_prompt = """You are a helpful HR policy assistant. You help employees understand company HR policies.

Your role is to:
1. Use the lookup_policy tool to find relevant policy information
2. Answer questions accurately based on the policy content
3. Be clear and concise in your responses
4. If a question isn't covered by the policies, say so honestly

Always cite which policy you're referencing when providing information."""

    messages = [
        {"role": "user", "content": question}
    ]

    # Agentic loop
    while True:
        response = llm.complete(
            system=system_prompt,
            messages=messages,
            tools=tools,
            max_tokens=1024
        )

        # Check if we're done (no tool use)
        stop_reason = response.stop_reason

        # Collect any text response
        text_response = llm.text_of(response)

        # Check for tool use
        tool_calls = [b for b in response.content if getattr(b, "type", "") == "tool_use"]

        if not tool_calls:
            # No tool calls, return the final response
            return text_response

        # Process tool calls
        tool_results = []
        for tool_call in tool_calls:
            if tool_call.name == "lookup_policy":
                policy_name = tool_call.input.get("policy_name")
                result = lookup_policy(policy_name, policies)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": result
                })

        # Add assistant response and tool results to messages
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})


def main():
    """Main entry point for the agent."""
    policies = load_policies()

    print("HR Policy Agent")
    print("=" * 50)
    print(f"Loaded {len(policies)} policies: {', '.join(policies.keys())}")
    print("=" * 50)
    print()

    while True:
        question = input("Ask a question about HR policies (or 'quit' to exit): ").strip()

        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if not question:
            continue

        print("\nAgent thinking...\n")
        answer = run_agent_loop(question, policies)
        print(f"Answer: {answer}\n")


if __name__ == "__main__":
    main()
