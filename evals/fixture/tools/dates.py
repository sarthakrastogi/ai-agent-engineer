from datetime import datetime

from langchain_core.tools import tool


@tool
def parse_date(text: str) -> str:
    """Parse a date the customer mentions into ISO format."""
    return datetime.fromisoformat(text).date().isoformat()
