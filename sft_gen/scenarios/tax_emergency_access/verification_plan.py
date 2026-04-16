"""Verification plan for tax_emergency_access."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "ceiling_view_requires_org_match_or_emergency_with_consent",
            "description": "Professional may viewDocument only when valid consent holds and either org match or emergency mode applies",
            "type": "implies",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(
                REFS,
                "ceiling_view_requires_org_match_or_emergency_with_consent.cedar",
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
            "name": "floor_view_emergency_with_consent",
            "description": "Professional must be permitted to viewDocument during emergency mode when valid consent holds",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(
                REFS,
                "floor_view_emergency_with_consent.cedar",
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
    ]
