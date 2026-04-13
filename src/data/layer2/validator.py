"""
Layer 2 Cedar policy validator.

Validates LLM-generated samples using the Cedar CLI:
  Step 1 — Syntax check:   cedar validate --schema ... --policies ...
  Step 2 — Schema check:   cedar validate --schema ... --policies ... (same call, checks type safety)
  Step 3 — Semantic check: cedar authorize ... for each test case

All file I/O uses a temporary directory that is cleaned up after each call.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Cedar CLI path resolution
# ---------------------------------------------------------------------------

def _find_cedar() -> str:
    return (
        os.environ.get("CEDAR")
        or shutil.which("cedar")
        or os.path.expanduser("~/.cargo/bin/cedar")
    )


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TestCaseResult:
    index: int
    principal: str
    action: str
    resource: str
    expected: str           # "ALLOW" or "DENY"
    actual: str             # "ALLOW" or "DENY"
    passed: bool
    error: str = ""         # Cedar CLI error message if the call failed


@dataclass
class ValidationResult:
    syntax_valid: bool = False
    schema_valid: bool = False
    test_cases: list[TestCaseResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def test_cases_passed(self) -> int:
        return sum(1 for tc in self.test_cases if tc.passed)

    @property
    def test_cases_total(self) -> int:
        return len(self.test_cases)

    @property
    def fully_valid(self) -> bool:
        """True only if syntax, schema, and all test cases pass."""
        return (
            self.syntax_valid
            and self.schema_valid
            and self.test_cases_total > 0
            and self.test_cases_passed == self.test_cases_total
        )

    def to_dict(self) -> dict:
        return {
            "syntax_valid": self.syntax_valid,
            "schema_valid": self.schema_valid,
            "test_cases_passed": self.test_cases_passed,
            "test_cases_total": self.test_cases_total,
            "fully_valid": self.fully_valid,
            "errors": self.errors,
            "test_case_details": [
                {
                    "index": tc.index,
                    "principal": tc.principal,
                    "action": tc.action,
                    "resource": tc.resource,
                    "expected": tc.expected,
                    "actual": tc.actual,
                    "passed": tc.passed,
                    "error": tc.error,
                }
                for tc in self.test_cases
            ],
        }


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

def validate_sample(sample: dict) -> ValidationResult:
    """
    Run all three validation steps on a generated sample.

    Args:
        sample: Parsed LLM response dict with keys:
                schema, cedar_policy, test_cases

    Returns:
        ValidationResult with per-step outcomes.
    """
    result = ValidationResult()
    cedar_bin = _find_cedar()
    tmp_dir = tempfile.mkdtemp(prefix="cedar_val_")

    try:
        schema_path = os.path.join(tmp_dir, "schema.cedarschema")
        policy_path = os.path.join(tmp_dir, "policy.cedar")
        entities_path = os.path.join(tmp_dir, "entities.json")

        with open(schema_path, "w", encoding="utf-8") as f:
            f.write(sample.get("schema", ""))
        with open(policy_path, "w", encoding="utf-8") as f:
            f.write(sample.get("cedar_policy", ""))

        # Step 1 + 2: syntax and schema validation (one cedar validate call)
        ok, err = _run_validate(cedar_bin, schema_path, policy_path)
        result.syntax_valid = ok
        result.schema_valid = ok
        if not ok:
            result.errors.append(err)
            return result   # no point running test cases if policy is invalid

        # Step 3: semantic check — run each test case
        test_cases = sample.get("test_cases", [])
        for i, tc in enumerate(test_cases):
            # Write entities for this test case
            entities = tc.get("entities", [])
            with open(entities_path, "w", encoding="utf-8") as f:
                json.dump(entities, f)

            tc_result = _run_authorize(
                cedar_bin=cedar_bin,
                schema_path=schema_path,
                policy_path=policy_path,
                entities_path=entities_path,
                principal=tc.get("principal", ""),
                action=tc.get("action", ""),
                resource=tc.get("resource", ""),
                context=tc.get("context", {}),
                expected=tc.get("expected_decision", ""),
                index=i,
            )
            result.test_cases.append(tc_result)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return result


# ---------------------------------------------------------------------------
# Cedar CLI wrappers
# ---------------------------------------------------------------------------

def _run_validate(
    cedar_bin: str,
    schema_path: str,
    policy_path: str,
) -> tuple[bool, str]:
    """
    Run `cedar validate --schema ... --policies ...`.

    Returns (success, error_message).
    """
    try:
        proc = subprocess.run(
            [cedar_bin, "validate", "--schema", schema_path, "--policies", policy_path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0:
            return True, ""
        return False, (proc.stderr or proc.stdout).strip()
    except subprocess.TimeoutExpired:
        return False, "cedar validate timed out"
    except FileNotFoundError:
        return False, f"cedar binary not found: {cedar_bin}"


def _run_authorize(
    cedar_bin: str,
    schema_path: str,
    policy_path: str,
    entities_path: str,
    principal: str,
    action: str,
    resource: str,
    context: dict,
    expected: str,
    index: int,
) -> TestCaseResult:
    """
    Run `cedar authorize ...` for one test case.

    Returns a TestCaseResult with actual vs expected decision.
    """
    context_json = json.dumps(context) if context else "{}"
    try:
        proc = subprocess.run(
            [
                cedar_bin, "authorize",
                "--schema",   schema_path,
                "--policies", policy_path,
                "--entities", entities_path,
                "--principal", principal,
                "--action",    action,
                "--resource",  resource,
                "--context",   context_json,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = proc.stdout.strip()
        # Cedar CLI outputs "ALLOW" or "DENY" as the first token on success
        actual = "ALLOW" if output.startswith("ALLOW") else "DENY"
        passed = actual == expected
        error = (proc.stderr or "").strip() if proc.returncode != 0 else ""
        return TestCaseResult(
            index=index,
            principal=principal,
            action=action,
            resource=resource,
            expected=expected,
            actual=actual,
            passed=passed,
            error=error,
        )
    except subprocess.TimeoutExpired:
        return TestCaseResult(
            index=index, principal=principal, action=action, resource=resource,
            expected=expected, actual="ERROR", passed=False,
            error="cedar authorize timed out",
        )
    except FileNotFoundError:
        return TestCaseResult(
            index=index, principal=principal, action=action, resource=resource,
            expected=expected, actual="ERROR", passed=False,
            error=f"cedar binary not found: {cedar_bin}",
        )
