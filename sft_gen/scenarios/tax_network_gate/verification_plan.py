"""Verification plan for tax_network_gate."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "org_match_consent_and_network_safety",
            "description": "Professional may viewDocument only when org match, valid consent, and onCorporateNetwork all hold",
            "type": "implies",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(REFS, "org_match_consent_and_network_safety.cedar"),
        },
        {
            "name": "must_view_org_match_with_consent_on_network",
            "description": "Professional must be permitted to viewDocument when org match, valid consent, and onCorporateNetwork all hold",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "must_view_org_match_with_consent_on_network.cedar"),
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
