"""Tests for the HR policy agent."""

import agent


def test_load_policies():
    """Test that policies are loaded correctly."""
    policies = agent.load_policies()
    assert len(policies) > 0
    assert "leave" in policies
    assert "remote-work" in policies
    assert "equipment" in policies
    print(f"✓ Loaded {len(policies)} policies")


def test_policy_lookup_tool():
    """Test the policy lookup tool definition."""
    policies = agent.load_policies()
    tool = agent.build_policy_lookup_tool(policies)

    assert tool["name"] == "lookup_policy"
    assert "input_schema" in tool
    assert tool["input_schema"]["properties"]["policy_name"]["enum"]
    print("✓ Policy lookup tool schema is valid")


def test_lookup_policy():
    """Test looking up a policy."""
    policies = agent.load_policies()

    # Test valid lookup
    result = agent.lookup_policy("leave", policies)
    assert "Annual leave" in result
    assert "20 days" in result
    print("✓ Successfully looked up leave policy")

    # Test invalid lookup
    result = agent.lookup_policy("nonexistent", policies)
    assert "not found" in result
    print("✓ Handles invalid policy lookup gracefully")


if __name__ == "__main__":
    test_load_policies()
    test_policy_lookup_tool()
    test_lookup_policy()
    print("\n✓ All tests passed!")
