"""
Tests for the HR policy agent.

Tests verify:
- Retrieval correctly ranks relevant policies
- Agent refuses out-of-scope questions
- Answers cite their sources
- Basic Q&A flows work end-to-end
"""

import pytest
from agent import retrieve_relevant_policies, answer_question, load_policies


@pytest.fixture
def policies():
    """Load policies once for all tests."""
    return load_policies()


class TestRetrieval:
    """Tests for policy retrieval."""

    def test_retrieve_leave_policy_for_annual_leave_question(self, policies):
        """Retrieval should find leave policy for leave questions."""
        results = retrieve_relevant_policies("How many days of annual leave do I get?", policies, top_k=3)
        assert len(results) > 0
        assert any("leave" in r.filename.lower() for r in results), \
            f"Expected leave policy in results, got {[r.filename for r in results]}"

    def test_retrieve_remote_work_for_remote_question(self, policies):
        """Retrieval should find remote work policy."""
        results = retrieve_relevant_policies("Can I work from home?", policies, top_k=3)
        assert len(results) > 0
        assert any("remote" in r.filename.lower() for r in results), \
            f"Expected remote-work policy in results, got {[r.filename for r in results]}"

    def test_retrieve_expenses_for_meal_question(self, policies):
        """Retrieval should find expenses policy for meal questions."""
        results = retrieve_relevant_policies("What's the meal allowance while travelling?", policies, top_k=3)
        assert len(results) > 0
        assert any("expenses" in r.filename.lower() for r in results), \
            f"Expected expenses policy in results, got {[r.filename for r in results]}"

    def test_retrieve_equipment_for_laptop_question(self, policies):
        """Retrieval should find equipment policy."""
        results = retrieve_relevant_policies("When do I get a new laptop?", policies, top_k=3)
        assert len(results) > 0
        assert any("equipment" in r.filename.lower() for r in results), \
            f"Expected equipment policy in results, got {[r.filename for r in results]}"

    def test_retrieve_travel_for_flight_question(self, policies):
        """Retrieval should find travel policy."""
        results = retrieve_relevant_policies("Do I need approval to book a flight?", policies, top_k=3)
        assert len(results) > 0
        assert any("travel" in r.filename.lower() for r in results), \
            f"Expected travel policy in results, got {[r.filename for r in results]}"

    def test_retrieve_respects_top_k(self, policies):
        """Retrieval should not return more than top_k results."""
        results = retrieve_relevant_policies("leave", policies, top_k=2)
        assert len(results) <= 2


class TestAnswerQuality:
    """Tests for answer quality."""

    def test_answer_cites_policy_document(self, policies):
        """Answers should cite which policy they come from."""
        answer = answer_question("How much annual leave do full-time employees get?", policies)
        # Should mention either the filename or a policy title
        assert any(
            term in answer.lower()
            for term in ["leave", "policy", "policy document", "from"]
        ), f"Answer should cite its source. Got: {answer}"

    def test_answer_is_not_empty(self, policies):
        """Answers should not be empty."""
        answer = answer_question("What is the parental leave policy?", policies)
        assert len(answer) > 10, "Answer should have substantial content"

    def test_answer_contains_relevant_info(self, policies):
        """Answers should contain relevant information from the policy."""
        answer = answer_question("How much annual leave do I accrue?", policies)
        # Should mention days or the number 20
        assert any(
            term in answer.lower()
            for term in ["day", "20", "annual", "accrue"]
        ), f"Answer should contain relevant details. Got: {answer}"


class TestScopeHandling:
    """Tests for handling out-of-scope questions."""

    def test_decline_non_policy_question(self, policies):
        """Agent should decline to answer non-HR-policy questions."""
        answer = answer_question("What's the capital of France?", policies)
        # Should indicate it's out of scope, not make up an answer
        assert not ("capital" in answer.lower() and "france" in answer.lower()), \
            "Agent should not answer geography questions"

    def test_decline_personal_advice_question(self, policies):
        """Agent should not give personal career advice."""
        answer = answer_question("Should I ask for a raise?", policies)
        # This isn't directly covered in policies, so should redirect to HR
        assert ("hr" in answer.lower() or "contact" in answer.lower() or "outside" in answer.lower() or
                "don't" in answer.lower()), \
            f"Agent should indicate this is outside scope. Got: {answer}"


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_qa_flow_leave(self, policies):
        """Test a complete Q&A flow for leave."""
        question = "I'm a full-time employee. How many days of leave do I get per year?"
        answer = answer_question(question, policies)
        assert len(answer) > 0
        assert answer not in ["", "I don't know"]

    def test_full_qa_flow_remote_work(self, policies):
        """Test a complete Q&A flow for remote work."""
        question = "How many days per week can I work remotely?"
        answer = answer_question(question, policies)
        assert len(answer) > 0
        assert answer not in ["", "I don't know"]

    def test_full_qa_flow_equipment(self, policies):
        """Test a complete Q&A flow for equipment."""
        question = "When do I get a new laptop?"
        answer = answer_question(question, policies)
        assert len(answer) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
