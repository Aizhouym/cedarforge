permit (
    principal is User,
    action == Action::"push",
    resource is Repository
)
when {
    (principal in resource.writers || resource.pushAllowlist.contains(principal)) &&
    !resource.isArchived
};
