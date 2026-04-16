"""Verification plan for tax_multi_professional."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "org_or_assignment_and_consent_safety",
            "description": "Professional may viewDocument only when ((org match OR direct assignment) AND valid consent)",
            "type": "implies",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(REFS, "org_or_assignment_and_consent_safety.cedar"),
        },
        {
            "name": "must_view_org_match_with_consent",
            "description": "Professional must be permitted to viewDocument when (org match AND valid consent)",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "must_view_org_match_with_consent.cedar"),
        },
        {
            "name": "must_view_assignment_with_consent",
            "description": "Professional must be permitted to viewDocument when (direct assignment AND valid consent)",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "must_view_assignment_with_consent.cedar"),
        },
        {
            "name": "liveness_view_document",
            "description": "Professional+viewDocument+Document has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
    ]
