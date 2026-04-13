"""
Layer 2 scenario matrix definition.

200 slots = 10 industries × 5 authorization models × 4 complexity levels.
Each slot specifies how many records to generate (target_count).
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------

INDUSTRIES: list[dict] = [
    {
        "id": "healthcare",
        "name": "Healthcare",
        "description": "Medical records, prescriptions, and department-level access control.",
        "example_entities": ["Patient", "Doctor", "Nurse", "Department", "MedicalRecord", "Prescription"],
        "example_actions": ["view_record", "edit_record", "prescribe", "discharge", "transfer_patient"],
    },
    {
        "id": "finance",
        "name": "Finance",
        "description": "Bank accounts, transactions, and risk-based approval workflows.",
        "example_entities": ["Account", "Transaction", "Employee", "Branch", "AuditLog"],
        "example_actions": ["view_account", "initiate_transfer", "approve_transaction", "generate_report"],
    },
    {
        "id": "education",
        "name": "Education",
        "description": "Courses, grades, and student privacy in a learning management system.",
        "example_entities": ["Student", "Instructor", "Course", "Assignment", "Grade", "Enrollment"],
        "example_actions": ["view_grade", "submit_assignment", "publish_grade", "enroll", "manage_course"],
    },
    {
        "id": "ecommerce",
        "name": "E-commerce",
        "description": "Product listings, orders, and seller/buyer role separation.",
        "example_entities": ["Buyer", "Seller", "Product", "Order", "Store", "Review"],
        "example_actions": ["view_product", "place_order", "manage_listing", "process_refund", "leave_review"],
    },
    {
        "id": "saas_multitenant",
        "name": "SaaS Multi-tenant",
        "description": "Strict tenant isolation with a narrow global-support cross-tenant read path.",
        "example_entities": ["User", "Tenant", "Resource", "ApiKey", "SupportTicket"],
        "example_actions": ["read_resource", "write_resource", "delete_resource", "manage_tenant"],
    },
    {
        "id": "government",
        "name": "Government",
        "description": "Classified documents, data sensitivity tiers, and cross-department workflows.",
        "example_entities": ["Officer", "Department", "Document", "Classification", "Workflow"],
        "example_actions": ["read_document", "approve_document", "classify", "transfer_case"],
    },
    {
        "id": "media",
        "name": "Media",
        "description": "Content publishing, moderation queues, and tiered subscriber access.",
        "example_entities": ["Author", "Editor", "Subscriber", "Article", "Video", "Comment"],
        "example_actions": ["publish_content", "moderate_comment", "watch_video", "edit_article"],
    },
    {
        "id": "iot",
        "name": "IoT",
        "description": "Smart device control, sensor data access, and firmware update authorization.",
        "example_entities": ["Device", "Owner", "Technician", "Gateway", "FirmwarePackage"],
        "example_actions": ["read_sensor", "control_device", "update_firmware", "pair_device"],
    },
    {
        "id": "gaming",
        "name": "Gaming",
        "description": "In-game item trading, chat moderation, and game-master privilege escalation.",
        "example_entities": ["Player", "GameMaster", "Item", "ChatRoom", "Guild", "Inventory"],
        "example_actions": ["trade_item", "send_message", "ban_player", "spawn_item", "manage_guild"],
    },
    {
        "id": "hr",
        "name": "HR",
        "description": "Payroll, leave requests, and performance reviews with separation of duties.",
        "example_entities": ["Employee", "Manager", "HRAdmin", "PayrollRecord", "LeaveRequest", "Review"],
        "example_actions": ["view_payroll", "approve_leave", "submit_review", "edit_payroll"],
    },
]

AUTH_MODELS: list[dict] = [
    {
        "id": "rbac",
        "name": "RBAC",
        "description": (
            "Role-Based Access Control. Access is determined by group membership. "
            "Use 'principal in RoleGroup' in policy scope or conditions."
        ),
    },
    {
        "id": "abac",
        "name": "ABAC",
        "description": (
            "Attribute-Based Access Control. Access is determined by attributes on the "
            "principal, resource, or context. Use 'when { resource.sensitivity == \"high\" }' style conditions."
        ),
    },
    {
        "id": "rebac",
        "name": "ReBAC",
        "description": (
            "Relationship-Based Access Control. Access is determined by entity relationships "
            "and hierarchy traversal, e.g. 'principal in resource.owner.team'."
        ),
    },
    {
        "id": "mixed",
        "name": "Mixed",
        "description": (
            "Combination of RBAC and ABAC. Roles gate coarse-grained access; "
            "attributes refine it. Use both group membership checks and attribute conditions."
        ),
    },
    {
        "id": "multi_policy",
        "name": "Multi-policy",
        "description": (
            "Multiple interacting policies including both permit and forbid rules. "
            "Demonstrates Cedar's deny-overrides logic and policy conflict resolution."
        ),
    },
]

COMPLEXITY_LEVELS: list[dict] = [
    {
        "id": "L1",
        "name": "Simple",
        "target_count": 4,
        "description": (
            "Single policy, single condition, direct equality or boolean check. "
            "Example: permit a specific role to perform one action on one resource type."
        ),
    },
    {
        "id": "L2",
        "name": "Moderate",
        "target_count": 4,
        "description": (
            "2–3 conditions combined with && or ||, one level of entity hierarchy via 'in'. "
            "Example: permit access when role matches AND resource is not archived."
        ),
    },
    {
        "id": "L3",
        "name": "Complex",
        "target_count": 4,
        "description": (
            "Multiple policies interacting, nested attribute traversal, or use of policy templates. "
            "Example: a permit with multiple conditions plus a forbid that overrides in certain cases."
        ),
    },
    {
        "id": "L4",
        "name": "Edge case",
        "target_count": 3,
        "description": (
            "Boundary and edge cases: 'unless' instead of 'when', negation of set membership, "
            "optional attribute guards with 'has', or policies that intentionally produce DENY "
            "for most inputs while allowing a narrow path."
        ),
    },
]


# ---------------------------------------------------------------------------
# Slot dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScenarioSlot:
    """One cell in the 10 × 5 × 4 scenario matrix."""
    slot_id: str                # e.g. "healthcare_rbac_l1"
    industry: dict
    auth_model: dict
    complexity: dict
    target_count: int           # how many records to generate for this slot

    @property
    def industry_id(self) -> str:
        return self.industry["id"]

    @property
    def auth_model_id(self) -> str:
        return self.auth_model["id"]

    @property
    def complexity_id(self) -> str:
        return self.complexity["id"]


# ---------------------------------------------------------------------------
# Matrix builder
# ---------------------------------------------------------------------------

def build_matrix() -> list[ScenarioSlot]:
    """
    Build the full 200-slot scenario matrix.

    Returns a list of ScenarioSlot objects sorted by
    (industry, auth_model, complexity).
    """
    slots: list[ScenarioSlot] = []
    for industry in INDUSTRIES:
        for auth_model in AUTH_MODELS:
            for complexity in COMPLEXITY_LEVELS:
                slot_id = f"{industry['id']}_{auth_model['id']}_{complexity['id'].lower()}"
                slots.append(
                    ScenarioSlot(
                        slot_id=slot_id,
                        industry=industry,
                        auth_model=auth_model,
                        complexity=complexity,
                        target_count=complexity["target_count"],
                    )
                )
    return slots


def matrix_summary() -> None:
    """Print a summary of the scenario matrix."""
    slots = build_matrix()
    total_records = sum(s.target_count for s in slots)
    print(f"Scenario matrix: {len(slots)} slots, {total_records} target records")
    print(f"  Industries   : {len(INDUSTRIES)}")
    print(f"  Auth models  : {len(AUTH_MODELS)}")
    print(f"  Complexity   : {[c['id'] for c in COMPLEXITY_LEVELS]}")
    print(f"  Per slot     : L1={COMPLEXITY_LEVELS[0]['target_count']}, "
          f"L2={COMPLEXITY_LEVELS[1]['target_count']}, "
          f"L3={COMPLEXITY_LEVELS[2]['target_count']}, "
          f"L4={COMPLEXITY_LEVELS[3]['target_count']}")


if __name__ == "__main__":
    matrix_summary()
