permit (
    principal is User,
    action == Action::"viewReport",
    resource is Report
)
when {
    principal in Role::"Role-B" &&
    !resource.isConfidential &&
    principal.allowedTagsForRole has "Role-B" &&
    !(principal.allowedTagsForRole["Role-B"] has production_status) &&
    !(principal.allowedTagsForRole["Role-B"] has country) &&
    !(principal.allowedTagsForRole["Role-B"] has stage) &&
    !(resource.workspace.tags has production_status) &&
    !(resource.workspace.tags has country) &&
    !(resource.workspace.tags has stage)
};
