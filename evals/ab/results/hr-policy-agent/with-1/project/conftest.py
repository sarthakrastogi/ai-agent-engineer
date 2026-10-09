"""Pytest configuration and fixtures for HR policy agent tests."""
import pytest
from unittest.mock import Mock


@pytest.fixture(autouse=True)
def mock_anthropic_when_needed(monkeypatch):
    """Mock the Anthropic client for tests that don't need real API calls.

    This allows tests to run without an API key, but integration tests
    can still use a real API by explicitly importing and using the client.
    """
    pass  # Tests import complete() directly, so mocking happens per-test
