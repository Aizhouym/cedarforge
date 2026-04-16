permit (
    principal is User,
    action == Action::"push",
    resource is Repository
)
when { resource.pushAllowlist.contains(principal) && !resource.isArchived };
