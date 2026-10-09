"""Tests for the HR policy agent."""
import pytest

from agent import answer_question, load_policies, build_system_prompt


class TestPoliciesLoading:
    def test_load_policies_returns_string(self):
        """Policies should load and return a non-empty string."""
        policies = load_policies()
        assert isinstance(policies, str)
        assert len(policies) > 0

    def test_load_policies_contains_key_sections(self):
        """Loaded policies should contain all policy documents."""
        policies = load_policies()
        assert "Leave policy" in policies
        assert "Remote work policy" in policies
        assert "Travel policy" in policies
        assert "Equipment policy" in policies
        assert "Expenses policy" in policies


class TestSystemPrompt:
    def test_system_prompt_includes_policies(self):
        """System prompt should embed the loaded policies."""
        policies = load_policies()
        prompt = build_system_prompt(policies)
        assert policies in prompt
        assert "HR policy assistant" in prompt
        assert "cite the relevant policy section" in prompt


class TestAgentResponses:
    """Integration tests for question answering.

    These tests verify the agent gives sensible answers and cites policies.
    """

    def test_leave_policy_question(self):
        """Agent should answer questions about leave policies."""
        answer = answer_question("How much annual leave do full-time employees get?")
        assert isinstance(answer, str)
        assert len(answer) > 0
        # Should cite the leave policy
        assert any(
            keyword in answer.lower()
            for keyword in ["20 days", "annual leave", "leave policy"]
        )

    def test_remote_work_question(self):
        """Agent should answer questions about remote work."""
        answer = answer_question("Can I work from home? How many days?")
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert any(
            keyword in answer.lower()
            for keyword in ["3 days", "remote", "manager", "agreement"]
        )

    def test_travel_approval_question(self):
        """Agent should answer questions about travel approvals."""
        answer = answer_question(
            "Who needs to approve my international flight?"
        )
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert any(
            keyword in answer.lower()
            for keyword in ["director", "approval", "travel"]
        )

    def test_equipment_policy_question(self):
        """Agent should answer questions about equipment."""
        answer = answer_question("How often do I get a new laptop?")
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert any(
            keyword in answer.lower()
            for keyword in ["3 years", "refresh", "equipment"]
        )

    def test_expenses_limit_question(self):
        """Agent should answer questions about expense limits."""
        answer = answer_question(
            "What's my meal allowance while travelling?"
        )
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert any(
            keyword in answer.lower()
            for keyword in ["80", "meal", "travelling", "nzd"]
        )

    def test_uncovered_question_handling(self):
        """Agent should acknowledge when policies don't cover a question."""
        answer = answer_question(
            "What's the salary for a software engineer?"
        )
        assert isinstance(answer, str)
        assert len(answer) > 0
        # Should indicate the policy doesn't cover this
        assert any(
            keyword in answer.lower()
            for keyword in ["not covered", "don't", "don't have", "no information"]
        )
