#!/usr/bin/env python3
"""
HR Policy Agent - answers employee questions about company HR policies.

Usage:
    python3 hr_agent.py "Your question here"
    python3 hr_agent.py  # Run with example questions

Environment:
    Set ANTHROPIC_API_KEY environment variable for API access.
"""

import json
import sys
import os
from pathlib import Path

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("Warning: anthropic library not available. Install with: pip install anthropic")

MODEL_ID = "claude-opus-5-5"

# Define tools for searching policies
tools = [
    {
        "name": "search_policies",
        "description": "Search for relevant HR policy information from the policies directory",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query about HR policies (e.g., 'annual leave', 'expenses', 'remote work')"
                }
            },
            "required": ["query"]
        }
    }
]

def load_policies():
    """Load all policy files from the policies directory."""
    policies = {}
    policies_dir = Path(__file__).parent / "policies"

    for policy_file in policies_dir.glob("*.md"):
        with open(policy_file, 'r') as f:
            policies[policy_file.stem] = f.read()

    return policies

def search_policies(query: str, policies: dict) -> str:
    """Search policies for relevant content based on a query."""
    query_lower = query.lower()
    results = []

    for policy_name, content in policies.items():
        # Search in both policy name and content
        if query_lower in policy_name.lower() or query_lower in content.lower():
            results.append(f"## {policy_name.replace('-', ' ').title()}\n{content}")

    if not results:
        return "No relevant policies found for that query."

    return "\n\n".join(results)

def handle_tool_call(tool_name: str, tool_input: dict, policies: dict) -> str:
    """Handle tool calls from the agent."""
    if tool_name == "search_policies":
        return search_policies(tool_input["query"], policies)
    return "Unknown tool"

def run_agent(user_question: str):
    """Run the HR policy agent to answer a question."""
    if not HAS_ANTHROPIC:
        print("\n❌ Error: anthropic library not installed")
        print("Install it with: pip install anthropic")
        return

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        return

    print(f"\n{'='*60}")
    print(f"Employee: {user_question}")
    print('='*60)

    # Initialize the Anthropic client (after checking for API key)
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    policies = load_policies()

    messages = [
        {
            "role": "user",
            "content": user_question
        }
    ]

    system_prompt = """You are a helpful HR policy assistant. Your role is to answer employee questions
about company HR policies accurately and clearly.

When an employee asks a question, use the search_policies tool to find relevant policy information.
Then provide a clear, helpful answer based on the policy information you find.

Be friendly and professional. If a policy doesn't cover their question, let them know and suggest
they contact the HR department for clarification."""

    # Agentic loop
    while True:
        response = client.messages.create(
            model=MODEL_ID,
            max_tokens=1024,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        # Check if we're done
        if response.stop_reason == "end_turn":
            # Extract final text response
            for block in response.content:
                if hasattr(block, 'text'):
                    print(f"\nAssistant: {block.text}")
            break

        # Handle tool use
        if response.stop_reason == "tool_use":
            # Process each content block
            tool_results = []
            assistant_content = []

            for block in response.content:
                assistant_content.append(block)
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_id = block.id

                    # Execute the tool
                    result = handle_tool_call(tool_name, tool_input, policies)

                    # Collect tool results
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result
                    })

            # Add assistant response to messages
            messages.append({
                "role": "assistant",
                "content": assistant_content
            })

            # Add tool results to messages
            messages.append({
                "role": "user",
                "content": tool_results
            })
        else:
            # Unexpected stop reason
            print(f"Unexpected stop reason: {response.stop_reason}")
            break

def main():
    """Main entry point."""
    print("🚀 HR Policy Agent Started")
    print("-" * 60)

    # Example questions to demonstrate the agent
    example_questions = [
        "How much annual leave do I get?",
        "Can I work from home?",
        "What's the policy on claiming meal expenses while travelling?",
        "When can I get a new laptop?",
        "What if I need parental leave?",
    ]

    if len(sys.argv) > 1:
        # Use question from command line
        user_question = " ".join(sys.argv[1:])
        run_agent(user_question)
    else:
        # Run example questions
        for question in example_questions:
            run_agent(question)

if __name__ == "__main__":
    main()
