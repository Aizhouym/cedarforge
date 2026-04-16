permit (
    principal is User,
    action == Action::"ReadWorkspace",
    resource is Workspace
) when {
    resource.isPublic
};
