permit (
    principal is User,
    action == Action::"pull",
    resource is Repository
)
when { resource.isPublic };
