#!/usr/bin/env python3
"""
Tests for the HR Policy Agent
"""

import sys
from pathlib import Path
from hr_agent_demo import search_policies, load_policies, get_relevant_answer

def test_policy_loading():
    """Test that policies can be loaded."""
    policies = load_policies()
    assert len(policies) > 0, "No policies loaded"
    assert "leave" in policies, "Leave policy not found"
    assert "expenses" in policies, "Expenses policy not found"
    assert "remote-work" in policies, "Remote work policy not found"
    assert "travel" in policies, "Travel policy not found"
    assert "equipment" in policies, "Equipment policy not found"
    print("✓ Policy loading test passed")

def test_search_leave():
    """Test search for leave policies."""
    policies = load_policies()
    results = search_policies("annual leave", policies)
    assert len(results) > 0, "No leave policies found"
    assert "leave" in results[0][0], "Leave policy not in results"
    print("✓ Leave policy search test passed")

def test_search_remote():
    """Test search for remote work policies."""
    policies = load_policies()
    results = search_policies("work from home", policies)
    assert len(results) > 0, "No remote work policies found"
    assert "remote" in results[0][0], "Remote work policy not in results"
    print("✓ Remote work policy search test passed")

def test_search_expenses():
    """Test search for expense policies."""
    policies = load_policies()
    results = search_policies("expense claims", policies)
    assert len(results) > 0, "No expense policies found"
    assert "expenses" in results[0][0], "Expenses policy not in results"
    print("✓ Expenses policy search test passed")

def test_search_travel():
    """Test search for travel policies."""
    policies = load_policies()
    results = search_policies("flight booking", policies)
    assert len(results) > 0, "No travel policies found"
    assert "travel" in results[0][0], "Travel policy not in results"
    print("✓ Travel policy search test passed")

def test_search_equipment():
    """Test search for equipment policies."""
    policies = load_policies()
    results = search_policies("laptop", policies)
    assert len(results) > 0, "No equipment policies found"
    assert "equipment" in results[0][0], "Equipment policy not in results"
    print("✓ Equipment policy search test passed")

def test_answer_generation():
    """Test that answers can be generated."""
    policies = load_policies()
    answer = get_relevant_answer("How much leave do I get?", policies)
    assert len(answer) > 0, "No answer generated"
    assert "20 days" in answer, "Leave amount not in answer"
    print("✓ Answer generation test passed")

def test_specific_queries():
    """Test specific employee queries."""
    policies = load_policies()

    test_cases = [
        ("How much annual leave do I get?", "20 days"),
        ("Can I work from home?", "remotely up to 3 days"),
        ("What meals can I claim?", "NZD 80"),
        ("When can I get a new laptop?", "3 years"),
        ("What about parental leave?", "26 weeks"),
    ]

    for query, expected in test_cases:
        answer = get_relevant_answer(query, policies)
        assert expected.lower() in answer.lower(), f"Expected '{expected}' in answer for '{query}'"
        print(f"✓ Query test passed: '{query}'")

def run_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("HR Policy Agent - Test Suite")
    print("="*60 + "\n")

    try:
        test_policy_loading()
        test_search_leave()
        test_search_remote()
        test_search_expenses()
        test_search_travel()
        test_search_equipment()
        test_answer_generation()
        test_specific_queries()

        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60 + "\n")
        return True

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
