permit (
    principal is User,
    action == Action::"UpdateWorkspace",
    resource is Workspace
) when {
    principal in Role::"Role-A" &&
    principal.allowedTagsForRole has "Role-A" &&
    resource.environment == "production" &&
    resource.tags has production_status &&
    !(resource.tags has country) &&
    !(resource.tags has stage) &&
    principal.allowedTagsForRole["Role-A"] has production_status &&
    !(principal.allowedTagsForRole["Role-A"] has country) &&
    !(principal.allowedTagsForRole["Role-A"] has stage) &&
    principal.allowedTagsForRole["Role-A"].production_status.containsAll(resource.tags.production_status)
};
