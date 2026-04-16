permit (
    principal is User,
    action == Action::"deploy",
    resource is Deployment
)
when {
    principal in resource.repo.maintainers &&
    resource.env != "production"
};
