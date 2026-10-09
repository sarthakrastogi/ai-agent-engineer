#!/usr/bin/env python3
"""
HR Policy Agent (Advanced)
An enhanced version with streaming, persistent history, and command support.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic

# Initialize the Anthropic client
client = Anthropic()


class HRPolicyAgent:
    """An agent that answers HR policy questions with state management."""

    def __init__(self, history_file: str = ".chat_history.json"):
        self.history_file = Path(history_file)
        self.policies = self.load_policies()
        self.system_prompt = self.build_system_prompt()
        self.conversation_history = self.load_history()

    def load_policies(self) -> dict:
        """Load all HR policies from the policies/ directory."""
        policies_dir = Path(__file__).parent / "policies"
        policies = {}

        if not policies_dir.exists():
            print(f"Error: Policies directory not found at {policies_dir}")
            sys.exit(1)

        for policy_file in sorted(policies_dir.glob("*.md")):
            with open(policy_file, "r") as f:
                policies[policy_file.stem] = f.read()

        return policies

    def build_system_prompt(self) -> str:
        """Build a system prompt that includes all HR policies."""
        policies_text = "\n\n".join(
            f"## {name.replace('_', ' ').title()}\n{content}"
            for name, content in self.policies.items()
        )

        return f"""You are an HR Policy Assistant for a company. Your job is to help employees understand and navigate the company's HR policies.

You have access to the following HR policies:

{policies_text}

Guidelines for your responses:
1. Answer questions based on the policies provided above.
2. Be clear and concise in your explanations.
3. If a policy is ambiguous or a question falls outside the policies, acknowledge the limitation and suggest contacting HR directly.
4. Always cite the specific policy section when providing information.
5. If you don't know the answer based on the policies, say so explicitly.
6. Be helpful and empathetic - you're helping employees understand their benefits and obligations.
7. For numerical values or dates, be precise and use the exact figures from the policies."""

    def load_history(self) -> list:
        """Load conversation history from file if it exists."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load history: {e}")
        return []

    def save_history(self):
        """Save conversation history to file."""
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.conversation_history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save history: {e}")

    def display_policies(self):
        """Display available policies."""
        print("\n" + "=" * 60)
        print("Available HR Policies:")
        print("=" * 60)
        for name in self.policies.keys():
            print(f"  • {name.replace('_', ' ').title()}")
        print()

    def display_help(self):
        """Display help information."""
        print("\n" + "=" * 60)
        print("Commands:")
        print("=" * 60)
        print("  /help        - Show this help message")
        print("  /policies    - List available policies")
        print("  /clear       - Clear conversation history")
        print("  /save        - Save conversation to file")
        print("  /load        - Load previous conversation")
        print("  /exit        - Exit the program")
        print()

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        self.history_file.unlink(missing_ok=True)
        print("\nConversation history cleared.")

    def ask_question(self, question: str) -> str:
        """Ask the agent a question and return the response."""
        self.conversation_history.append({
            "role": "user",
            "content": question
        })

        try:
            response = client.messages.create(
                model="claude-opus-5-5",
                max_tokens=1024,
                system=self.system_prompt,
                messages=self.conversation_history
            )

            assistant_message = response.content[0].text
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            self.save_history()
            return assistant_message

        except Exception as e:
            # Remove the user message from history if there was an error
            self.conversation_history.pop()
            raise e

    def run(self):
        """Main conversation loop."""
        print("=" * 60)
        print("HR Policy Agent (Advanced)")
        print("=" * 60)
        print("\nWelcome! I'm here to help you understand company HR policies.")
        print("Type '/help' for commands or ask me anything about our policies.\n")

        if self.conversation_history:
            print(f"Loaded {len(self.conversation_history) // 2} previous messages from history.\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                if user_input == "/exit" or user_input == "/quit":
                    print("\nThank you for using the HR Policy Agent. Goodbye!")
                    break
                elif user_input == "/help":
                    self.display_help()
                elif user_input == "/policies":
                    self.display_policies()
                elif user_input == "/clear":
                    self.clear_history()
                elif user_input == "/save":
                    self.save_history()
                    print(f"History saved to {self.history_file}")
                elif user_input == "/load":
                    self.conversation_history = self.load_history()
                    msg_count = len(self.conversation_history) // 2
                    print(f"Loaded {msg_count} previous messages.")
                else:
                    print(f"Unknown command: {user_input}. Type '/help' for available commands.")
                continue

            # Process regular question
            try:
                print()
                response = self.ask_question(user_input)
                print(f"Assistant: {response}\n")
            except Exception as e:
                print(f"Error: {e}\n")


def main():
    """Entry point."""
    agent = HRPolicyAgent()
    agent.run()


if __name__ == "__main__":
    main()
