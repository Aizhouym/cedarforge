permit (
    principal is User,
    action == Action::"UpdateWorkspace",
    resource is Workspace
) when {
    principal in Role::"Role-D" &&
    principal.allowedTagsForRole has "Role-D" &&
    resource.tags has stage &&
    !(resource.tags has production_status) &&
    !(resource.tags has country) &&
    principal.allowedTagsForRole["Role-D"] has stage &&
    !(principal.allowedTagsForRole["Role-D"] has production_status) &&
    !(principal.allowedTagsForRole["Role-D"] has country) &&
    principal.allowedTagsForRole["Role-D"].stage.containsAll(resource.tags.stage)
};
