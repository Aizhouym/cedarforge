"""Verification plan for tax_review."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "view_document_org_match_and_consent_safety",
            "description": "Professional may viewDocument only when (org match AND valid consent)",
            "type": "implies",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(REFS, "ceiling_viewDocument.cedar"),
        },
        {
            "name": "approve_document_supervisor_and_consent_safety",
            "description": "Supervisor may approveDocument only when supervised org matches the document owner organization and consent is valid",
            "type": "implies",
            "principal_type": "Taxpreparer::Supervisor",
            "action": "Taxpreparer::Action::\"approveDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(REFS, "ceiling_approveDocument.cedar"),
        },
        {
            "name": "must_view_org_match_with_consent",
            "description": "Professional must be permitted to viewDocument when (org match AND valid consent)",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "floor_viewDocument.cedar"),
        },
        {
            "name": "must_approve_supervised_org_with_consent",
            "description": "Supervisor must be permitted to approveDocument when supervised org matches and valid consent is present",
            "type": "floor",
            "principal_type": "Taxpreparer::Supervisor",
            "action": "Taxpreparer::Action::\"approveDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "floor_approveDocument.cedar"),
        },
        {
            "name": "liveness_view_document",
            "description": "Professional+viewDocument+Document has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
        {
            "name": "liveness_approve_document",
            "description": "Supervisor+approveDocument+Document has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Supervisor",
            "action": "Taxpreparer::Action::\"approveDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
    ]
