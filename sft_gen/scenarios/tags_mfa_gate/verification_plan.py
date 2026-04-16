"""Verification plan for tags_mfa_gate."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "ceiling_update_workspace",
            "description": "UpdateWorkspace is only permitted for Role-A members whose Role-A tags match the workspace tags and MFA is verified",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_update_workspace.cedar"),
        },
        {
            "name": "ceiling_delete_workspace",
            "description": "DeleteWorkspace is only permitted for Role-A members whose Role-A tags match the workspace tags and MFA is verified",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"DeleteWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_delete_workspace.cedar"),
        },
        {
            "name": "ceiling_read_workspace",
            "description": "ReadWorkspace is only permitted for Role-A members with matching Role-A tags or Role-B members with matching Role-B tags",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_read_workspace.cedar"),
        },
        {
            "name": "floor_role_a_update",
            "description": "A Role-A member with the Role-A record present and no tag dimensions must be permitted to UpdateWorkspace on an untagged workspace when MFA is verified",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_role_a_update.cedar"),
        },
        {
            "name": "floor_role_a_delete",
            "description": "A Role-A member with the Role-A record present and no tag dimensions must be permitted to DeleteWorkspace on an untagged workspace when MFA is verified",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"DeleteWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_role_a_delete.cedar"),
        },
        {
            "name": "floor_role_b_read",
            "description": "A Role-B member with the Role-B record present and no tag dimensions must be permitted to ReadWorkspace on an untagged workspace",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_role_b_read.cedar"),
        },
        {
            "name": "floor_role_a_read_all_wildcard",
            "description": "A Role-A member whose Role-A production_status contains ALL must be permitted to ReadWorkspace when only that dimension is present",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_role_a_read_all_wildcard.cedar"),
        },
        {
            "name": "liveness_update_workspace",
            "description": "UpdateWorkspace policy is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
        },
        {
            "name": "liveness_delete_workspace",
            "description": "DeleteWorkspace policy is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"DeleteWorkspace\"",
            "resource_type": "Workspace",
        },
        {
            "name": "liveness_read_workspace",
            "description": "ReadWorkspace policy is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
        },
    ]
