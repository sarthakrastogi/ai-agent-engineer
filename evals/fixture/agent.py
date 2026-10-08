"""Support triage agent: classifies a ticket, looks up the order, drafts a reply."""
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from tools.dates import parse_date
from tools.orders import lookup_order

SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "triage.md").read_text()

model = ChatAnthropic(model="claude-sonnet-5-5", max_tokens=1024)
agent = create_react_agent(model, tools=[lookup_order, parse_date], prompt=SYSTEM_PROMPT)


def handle(ticket: str) -> str:
    resp = agent.invoke({"messages": [("user", ticket)]})
    return resp["messages"][-1].content
