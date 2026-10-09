#!/usr/bin/env python3
"""Tests for the HR policy agent."""

import os
from unittest.mock import Mock, patch
import agent


def test_load_policies():
    """Test that policies are loaded correctly."""
    policies = agent.load_policies()

    # Check that key policies are included
    assert "Leave policy" in policies
    assert "Remote work policy" in policies
    assert "Equipment policy" in policies

    # Check that specific content is present
    assert "20 days of annual leave" in policies
    assert "3 days per week" in policies
    assert "laptop refresh every 3 years" in policies

    print("✓ test_load_policies passed")


def test_create_system_prompt():
    """Test that system prompt is created correctly."""
    test_context = "Test policy content"
    prompt = agent.create_system_prompt(test_context)

    assert "helpful" in prompt.lower() and "assistant" in prompt.lower()
    assert "Test policy content" in prompt
    assert "employee questions" in prompt.lower()

    print("✓ test_create_system_prompt passed")


def test_answer_question():
    """Test answering a question using mocked LLM."""
    # Mock the llm.complete function
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Mock answer about annual leave")]

    with patch("llm.complete", return_value=mock_response):
        policies = agent.load_policies()
        answer = agent.answer_question(
            "How much annual leave do I get?",
            policies
        )

        assert answer == "Mock answer about annual leave"

    print("✓ test_answer_question passed")


def test_answer_question_with_real_llm():
    """Test answering a real question with the actual API."""
    # Skip if API key not available
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⊘ test_answer_question_with_real_llm skipped (no API key)")
        return

    policies = agent.load_policies()
    answer = agent.answer_question(
        "How much annual leave do I get?",
        policies
    )

    # Check that the answer mentions the leave policy
    assert answer.strip()  # Non-empty response
    assert "20 days" in answer or "annual leave" in answer.lower()

    print("✓ test_answer_question_with_real_llm passed")


if __name__ == "__main__":
    test_load_policies()
    test_create_system_prompt()
    test_answer_question()
    test_answer_question_with_real_llm()
    print("\nAll tests passed!")
