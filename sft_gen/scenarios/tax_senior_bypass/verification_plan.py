"""Verification plan for tax_senior_bypass."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "professional_view_safety",
            "description": "Professional may viewDocument only when org match and valid consent hold, and sensitive documents additionally require HQ in consent",
            "type": "implies",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(REFS, "professional_view_safety.cedar"),
        },
        {
            "name": "supervisor_view_safety",
            "description": "Supervisor may viewDocument only when supervised organization match and valid consent hold",
            "type": "implies",
            "principal_type": "Taxpreparer::Supervisor",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(REFS, "supervisor_view_safety.cedar"),
        },
        {
            "name": "professional_must_view_nonsensitive_with_consent",
            "description": "Professional must be permitted to view non-sensitive documents when org match and valid consent hold",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "professional_must_view_nonsensitive_with_consent.cedar"),
        },
        {
            "name": "professional_must_view_sensitive_with_hq",
            "description": "Professional must be permitted to view sensitive documents when org match, valid consent, and HQ are present",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "professional_must_view_sensitive_with_hq.cedar"),
        },
        {
            "name": "supervisor_must_view_sensitive_without_hq",
            "description": "Supervisor must be permitted to view sensitive documents with valid consent even without HQ in the consent region list",
            "type": "floor",
            "principal_type": "Taxpreparer::Supervisor",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "supervisor_must_view_sensitive_without_hq.cedar"),
        },
        {
            "name": "liveness_professional_view_document",
            "description": "Professional plus viewDocument plus Document has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
        {
            "name": "liveness_supervisor_view_document",
            "description": "Supervisor plus viewDocument plus Document has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Supervisor",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
    ]
