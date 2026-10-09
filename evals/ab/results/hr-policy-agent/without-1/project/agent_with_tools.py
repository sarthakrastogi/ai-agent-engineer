#!/usr/bin/env python3
"""Extended HR Policy Agent with tool use capabilities.

This version demonstrates how to add structured tool use to the agent,
such as fetching employee data or updating policy information.
"""

import json
from pathlib import Path
import llm
import agent


# Define tools available to the agent
TOOLS = [
    {
        "name": "get_employee_leave_balance",
        "description": "Get an employee's current leave balance. This is a placeholder that would connect to an HR system.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "The employee's ID or email"
                }
            },
            "required": ["employee_id"]
        }
    },
    {
        "name": "get_policy_version",
        "description": "Get the current version and effective date of a specific policy",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_name": {
                    "type": "string",
                    "description": "Name of the policy (e.g., 'leave', 'remote-work', 'equipment')"
                }
            },
            "required": ["policy_name"]
        }
    }
]


def handle_tool_call(tool_name: str, tool_input: dict) -> str:
    """Handle tool calls from the agent.

    In a real implementation, these would integrate with actual HR systems.
    """
    if tool_name == "get_employee_leave_balance":
        employee_id = tool_input.get("employee_id")
        # Placeholder: would query actual HR system
        return json.dumps({
            "employee_id": employee_id,
            "annual_leave_balance": 12.5,
            "sick_leave_balance": 8,
            "last_updated": "2026-10-09"
        })

    elif tool_name == "get_policy_version":
        policy_name = tool_input.get("policy_name")
        # Placeholder: would fetch actual policy metadata
        policies_meta = {
            "leave": {"version": "3", "effective_date": "2026-04-01"},
            "remote-work": {"version": "2", "effective_date": "2026-01-15"},
            "equipment": {"version": "1", "effective_date": "2025-06-01"}
        }
        if policy_name in policies_meta:
            return json.dumps(policies_meta[policy_name])
        else:
            return json.dumps({"error": f"Policy '{policy_name}' not found"})

    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


def chat_with_tools(policies_context: str):
    """Run an interactive chat session with tool support."""
    system_prompt = agent.create_system_prompt(policies_context)
    messages = []

    print("HR Policy Assistant (with Tool Support)")
    print("=" * 50)
    print("Ask me anything about company HR policies.")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except EOFError:
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("Thank you for using the HR Policy Assistant. Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        # Keep calling the API until we get a final response
        while True:
            response = llm.complete(
                system=system_prompt,
                messages=messages,
                tools=TOOLS,
                max_tokens=1024
            )

            # Check if we got tool use or text
            has_tool_use = False
            for content_block in response.content:
                if getattr(content_block, "type", "") == "tool_use":
                    has_tool_use = True
                    tool_name = content_block.name
                    tool_input = content_block.input

                    print(f"\n[Agent is calling tool: {tool_name}]")

                    # Handle the tool call
                    tool_result = handle_tool_call(tool_name, tool_input)

                    # Add assistant response with tool use to messages
                    messages.append({"role": "assistant", "content": response.content})

                    # Add tool result to messages
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": tool_result
                            }
                        ]
                    })

            # If no tool use, we have our final response
            if not has_tool_use:
                assistant_response = llm.text_of(response)
                messages.append({"role": "assistant", "content": assistant_response})
                print(f"\nAssistant: {assistant_response}\n")
                break


if __name__ == "__main__":
    import sys

    # Load all policies
    policies_context = agent.load_policies()

    # Run with tool support
    chat_with_tools(policies_context)
