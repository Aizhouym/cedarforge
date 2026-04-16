"""Verification plan for tax_deadline_gate."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "view_org_match_and_consent_safety",
            "description": "Professional may viewDocument only when org match and valid consent hold",
            "type": "implies",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(REFS, "view_org_match_and_consent_safety.cedar"),
        },
        {
            "name": "edit_org_match_consent_and_deadline_safety",
            "description": "Professional may editDocument only when org match, valid consent, and now not past filingDeadline hold",
            "type": "implies",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"editDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(REFS, "edit_org_match_consent_and_deadline_safety.cedar"),
        },
        {
            "name": "view_must_org_match_with_consent",
            "description": "Professional must be permitted to viewDocument when org match and valid consent hold",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "view_must_org_match_with_consent.cedar"),
        },
        {
            "name": "edit_must_org_match_with_consent_before_deadline",
            "description": "Professional must be permitted to editDocument when org match and valid consent hold and now is not past filingDeadline",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"editDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "edit_must_org_match_with_consent_before_deadline.cedar"),
        },
        {
            "name": "liveness_view_document",
            "description": "Professional plus viewDocument plus Document has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
        {
            "name": "liveness_edit_document",
            "description": "Professional plus editDocument plus Document has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"editDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
    ]
