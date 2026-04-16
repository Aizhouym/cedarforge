"""Verification plan for tax_org_hierarchy."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "org_or_parent_match_and_consent_safety",
            "description": "Professional may viewDocument only when direct org match or parent-org match holds, and valid consent holds",
            "type": "implies",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(REFS, "org_or_parent_match_and_consent_safety.cedar"),
        },
        {
            "name": "must_view_direct_org_match_with_consent",
            "description": "Professional must be permitted to viewDocument when direct org match and valid consent hold",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "must_view_direct_org_match_with_consent.cedar"),
        },
        {
            "name": "must_view_parent_org_match_with_consent",
            "description": "Professional must be permitted to viewDocument when parent-org match and valid consent hold",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "must_view_parent_org_match_with_consent.cedar"),
        },
        {
            "name": "liveness_view_document",
            "description": "Professional plus viewDocument plus Document has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
    ]
