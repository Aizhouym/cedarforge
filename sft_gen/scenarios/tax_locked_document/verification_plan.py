"""Verification plan for tax_locked_document."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "ceiling_view_requires_org_match_with_consent",
            "description": "Professional may viewDocument only when org match and valid consent both hold",
            "type": "implies",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(
                REFS,
                "ceiling_view_requires_org_match_with_consent.cedar",
            ),
        },
        {
            "name": "floor_view_org_match_with_consent",
            "description": "Professional must be permitted to viewDocument when org match and valid consent both hold",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(
                REFS,
                "floor_view_org_match_with_consent.cedar",
            ),
        },
        {
            "name": "liveness_view_document",
            "description": "viewDocument is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
        {
            "name": "ceiling_edit_requires_org_match_consent_and_unlocked",
            "description": "Professional may editDocument only when org match, valid consent, and unlocked document all hold",
            "type": "implies",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"editDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(
                REFS,
                "ceiling_edit_requires_org_match_consent_and_unlocked.cedar",
            ),
        },
        {
            "name": "floor_edit_org_match_with_consent_and_unlocked",
            "description": "Professional must be permitted to editDocument when org match, valid consent, and unlocked document all hold",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"editDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(
                REFS,
                "floor_edit_org_match_with_consent_and_unlocked.cedar",
            ),
        },
        {
            "name": "liveness_edit_document",
            "description": "editDocument is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"editDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
    ]
