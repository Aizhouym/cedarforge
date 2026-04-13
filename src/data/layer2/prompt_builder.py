"""
Layer 2 prompt builder.

Builds structured prompts for each scenario slot.
The LLM is expected to return a JSON object with these fields:

    {
        "schema": "<cedarschema text>",
        "nl_requirement": "<natural language description of the policy intent>",
        "cedar_policy": "<one or more Cedar policy statements>",
        "test_cases": [
            {
                "principal": "User::\"alice\"",
                "action": "Action::\"read\"",
                "resource": "Document::\"doc1\"",
                "context": {},
                "entities": [],
                "expected_decision": "ALLOW",
                "explanation": "alice is a member of the readers group"
            }
        ]
    }
"""

from __future__ import annotations

import json
from .matrix import ScenarioSlot


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert in the Cedar policy language developed by AWS.
Your task is to generate syntactically correct, semantically meaningful
Cedar access-control training examples.

Cedar syntax rules you must follow:
- Every policy ends with a semicolon ;
- Entity references use the format: Type::"id"
- Conditions go inside when { } or unless { } with curly braces, not parentheses
- Scope elements (principal, action, resource) are separated by commas
- The 'in' operator checks entity hierarchy membership (transitive)
- The 'has' operator checks if an optional attribute exists before accessing it
- String comparisons use == not =
- Sets use the syntax: [elem1, elem2]
- Action groups use: action in [Action::"read", Action::"write"]
"""


# ---------------------------------------------------------------------------
# Per-slot user prompt
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATE = """\
Generate a Cedar policy training example for the following scenario.

## Scenario
- Industry: {industry_name} — {industry_description}
- Authorization model: {auth_model_name} — {auth_model_description}
- Complexity level: {complexity_id} ({complexity_name}) — {complexity_description}

## Suggested entity types (adapt as needed)
{example_entities}

## Suggested actions (adapt as needed)
{example_actions}

## Requirements
1. Design a realistic Cedar Schema (.cedarschema format) for this scenario.
2. Write a natural language description of ONE concrete access-control requirement.
3. Write the Cedar policy (or policies) that implement that requirement.
   - For complexity {complexity_id}, {complexity_instruction}
4. Provide {test_case_count} authorization test cases:
   - Include both ALLOW and DENY cases where applicable.
   - Each test case must include an "explanation" field.
   - The "entities" field is a JSON array in Cedar entity format:
     [{{"uid": {{"type": "User", "id": "alice"}}, "attrs": {{}}, "parents": []}}]

## Output format
Respond with a single JSON object. No markdown, no explanation outside the JSON.

{{
    "schema": "<cedarschema text>",
    "nl_requirement": "<natural language description>",
    "cedar_policy": "<Cedar policy text>",
    "test_cases": [
        {{
            "principal": "Type::\"id\"",
            "action": "Action::\"name\"",
            "resource": "Type::\"id\"",
            "context": {{}},
            "entities": [],
            "expected_decision": "ALLOW or DENY",
            "explanation": "reason"
        }}
    ]
}}
"""

# Complexity-specific instructions for the policy writing step
_COMPLEXITY_INSTRUCTIONS: dict[str, str] = {
    "L1": (
        "write exactly ONE permit or forbid statement with a single condition "
        "(or no condition). Keep scope and when-clause minimal."
    ),
    "L2": (
        "write ONE policy with 2–3 conditions connected by && or ||, "
        "or use one level of entity hierarchy with the 'in' operator."
    ),
    "L3": (
        "write 2–3 policies that interact (e.g. a broad permit plus a narrowing forbid), "
        "or use nested attribute traversal (resource.owner.department), "
        "or demonstrate a policy template pattern."
    ),
    "L4": (
        "write a policy that uses 'unless' instead of 'when', or combines 'has' guards "
        "with negation, or covers a boundary case where most requests are DENY "
        "and only a narrow path is ALLOW."
    ),
}

# Number of test cases per complexity level
_TEST_CASE_COUNTS: dict[str, int] = {
    "L1": 3,
    "L2": 4,
    "L3": 5,
    "L4": 4,
}


def build_prompt(slot: ScenarioSlot) -> tuple[str, str]:
    """
    Build the (system_prompt, user_prompt) pair for a scenario slot.

    Returns:
        A tuple of (system_prompt, user_prompt) strings.
    """
    complexity_id = slot.complexity_id
    user_prompt = _PROMPT_TEMPLATE.format(
        industry_name=slot.industry["name"],
        industry_description=slot.industry["description"],
        auth_model_name=slot.auth_model["name"],
        auth_model_description=slot.auth_model["description"],
        complexity_id=complexity_id,
        complexity_name=slot.complexity["name"],
        complexity_description=slot.complexity["description"],
        example_entities=", ".join(slot.industry["example_entities"]),
        example_actions=", ".join(slot.industry["example_actions"]),
        complexity_instruction=_COMPLEXITY_INSTRUCTIONS[complexity_id],
        test_case_count=_TEST_CASE_COUNTS[complexity_id],
    )
    return SYSTEM_PROMPT, user_prompt


def parse_response(raw_response: str) -> dict | None:
    """
    Parse a raw LLM response string into a structured dict.

    Handles common LLM formatting issues:
    - Strips markdown code fences (```json ... ```)
    - Strips leading/trailing whitespace

    Returns the parsed dict, or None if parsing fails.
    """
    text = raw_response.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove opening fence (```json or ```)
        lines = lines[1:]
        # Remove closing fence
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def validate_response_schema(parsed: dict) -> tuple[bool, list[str]]:
    """
    Check that a parsed LLM response has all required fields with non-empty values.

    Returns:
        (is_valid, list_of_error_messages)
    """
    errors: list[str] = []
    required_fields = ["schema", "nl_requirement", "cedar_policy", "test_cases"]

    for field in required_fields:
        if field not in parsed:
            errors.append(f"Missing required field: {field}")
        elif not parsed[field]:
            errors.append(f"Field is empty: {field}")

    if "test_cases" in parsed and isinstance(parsed["test_cases"], list):
        for i, tc in enumerate(parsed["test_cases"]):
            for key in ("principal", "action", "resource", "expected_decision"):
                if key not in tc:
                    errors.append(f"test_cases[{i}] missing field: {key}")
            if "expected_decision" in tc:
                if tc["expected_decision"] not in ("ALLOW", "DENY"):
                    errors.append(
                        f"test_cases[{i}].expected_decision must be ALLOW or DENY, "
                        f"got: {tc['expected_decision']!r}"
                    )

    return (len(errors) == 0, errors)
