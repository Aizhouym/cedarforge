"""Verification plan for tax_auditor_page_limit."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "org_match_and_consent_safety",
            "description": "Professional may viewDocument only when org match and valid consent hold",
            "type": "implies",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(REFS, "org_match_and_consent_safety.cedar"),
        },
        {
            "name": "auditor_scope_consent_and_page_limit_safety",
            "description": "Auditor may auditDocument only when auditScope contains the document serviceline, consent is valid, and pageCount is at most 100",
            "type": "implies",
            "principal_type": "Taxpreparer::Auditor",
            "action": "Taxpreparer::Action::\"auditDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(REFS, "auditor_scope_consent_and_page_limit_safety.cedar"),
        },
        {
            "name": "must_view_org_match_with_consent",
            "description": "Professional must be permitted to viewDocument when org match and valid consent hold",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "must_view_org_match_with_consent.cedar"),
        },
        {
            "name": "must_audit_scope_with_consent_and_small_page_count",
            "description": "Auditor must be permitted to auditDocument when audit scope matches, consent is valid, and pageCount is at most 100",
            "type": "floor",
            "principal_type": "Taxpreparer::Auditor",
            "action": "Taxpreparer::Action::\"auditDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "must_audit_scope_with_consent_and_small_page_count.cedar"),
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
            "name": "liveness_audit_document",
            "description": "Auditor+auditDocument+Document has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Auditor",
            "action": "Taxpreparer::Action::\"auditDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
    ]
