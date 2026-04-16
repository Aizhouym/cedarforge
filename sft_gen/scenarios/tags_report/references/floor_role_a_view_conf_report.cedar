permit (
    principal is User,
    action == Action::"viewReport",
    resource is Report
)
when {
    principal in Role::"Role-A" &&
    resource.isConfidential &&
    principal.allowedTagsForRole has "Role-A" &&
    !(principal.allowedTagsForRole["Role-A"] has production_status) &&
    !(principal.allowedTagsForRole["Role-A"] has country) &&
    !(principal.allowedTagsForRole["Role-A"] has stage) &&
    !(resource.workspace.tags has production_status) &&
    !(resource.workspace.tags has country) &&
    !(resource.workspace.tags has stage)
};
