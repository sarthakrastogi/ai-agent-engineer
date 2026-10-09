"""
Test suite for model migration verification.
Compares Opus and Haiku on the eval set.

Run with: MODEL=claude-opus-5-5 python -m pytest tests/test_model_migration.py -v
Then:     MODEL=claude-haiku-5-5 python -m pytest tests/test_model_migration.py -v
"""
import json
import os
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from bot import reply

EVAL_CASES_PATH = Path(__file__).parent.parent / "evals" / "cases.jsonl"
CURRENT_MODEL = os.environ.get("MODEL", "claude-opus-5-5")


def load_eval_cases():
    """Load evaluation cases from cases.jsonl."""
    cases = []
    with open(EVAL_CASES_PATH) as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    return cases


@pytest.fixture
def eval_cases():
    return load_eval_cases()


@pytest.mark.parametrize("case_idx,case", enumerate(load_eval_cases()), ids=lambda x: f"case_{x[0]}")
def test_eval_case(case_idx, case):
    """Test each eval case and check required strings are in response."""
    output = reply(case["messages"]).lower()

    # Check must_include
    for required_str in case.get("must_include", []):
        assert required_str.lower() in output, \
            f"Case {case_idx}: Missing required string '{required_str}' in output: {output}"

    # Check must_not_include
    for forbidden_str in case.get("must_not_include", []):
        assert forbidden_str.lower() not in output, \
            f"Case {case_idx}: Found forbidden string '{forbidden_str}' in output: {output}"


def test_model_in_use(eval_cases):
    """Verify which model is currently being used."""
    print(f"\n\nRunning evals with MODEL={CURRENT_MODEL}\n")


def test_all_cases_pass(eval_cases):
    """Aggregate test: all cases must pass."""
    results = []
    for idx, case in enumerate(eval_cases):
        try:
            output = reply(case["messages"]).lower()
            passed = all(s.lower() in output for s in case.get("must_include", [])) and \
                     not any(s.lower() in output for s in case.get("must_not_include", []))
            results.append(passed)
        except Exception as e:
            print(f"Case {idx} error: {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)
    print(f"\n\nModel: {CURRENT_MODEL}")
    print(f"Pass rate: {passed}/{total} ({100*passed/total:.0f}%)\n")

    # Require ≥80% pass rate for Haiku, ≥90% for Opus
    min_rate = 0.80 if "haiku" in CURRENT_MODEL.lower() else 0.90
    assert passed / total >= min_rate, \
        f"Pass rate {100*passed/total:.0f}% below threshold {100*min_rate:.0f}%"
