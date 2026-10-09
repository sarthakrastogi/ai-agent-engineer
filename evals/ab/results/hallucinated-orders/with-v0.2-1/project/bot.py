"""Parcelly support bot: answers customer chats about orders, deliveries and returns."""
from llm import complete, text_of, process_tool_call

SYSTEM_PROMPT = """You are Parcelly's friendly support assistant. Help customers with
questions about their orders, delivery dates and returns.

IMPORTANT: Always use the lookup_order tool to fetch real order data. Never make up order numbers or dates.
If you don't have the information from a tool call, say you can't find it.
Keep replies under 80 words."""


def reply(history: list[dict]) -> str:
    """history: [{"role": "user"|"assistant", "content": str}, ...]

    Runs an agentic loop: calls the model, processes tool calls, and returns the final text response.
    """
    messages = list(history)  # copy to avoid mutating input

    # Agentic loop: keep calling until we get text, not a tool call
    while True:
        response = complete(system=SYSTEM_PROMPT, messages=messages)

        # Check if model wants to call a tool
        tool_uses = [b for b in response.content if getattr(b, "type", "") == "tool_use"]
        text_blocks = [b for b in response.content if getattr(b, "type", "") == "text"]

        # If no tool use, return the text
        if not tool_uses:
            return text_of(response)

        # Process tool calls and add them to the conversation
        # First, add the assistant's response (which includes tool_use blocks)
        messages.append({
            "role": "assistant",
            "content": response.content
        })

        # Then add tool results
        tool_results = []
        for tool_use in tool_uses:
            result = process_tool_call(tool_use.name, tool_use.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result
            })

        messages.append({
            "role": "user",
            "content": tool_results
        })

        # Loop continues to get final text response


if __name__ == "__main__":
    import sys
    print(reply([{"role": "user", "content": " ".join(sys.argv[1:])}]))
