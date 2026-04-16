permit (
    principal is User,
    action == Action::"deploy",
    resource is Deployment
)
when {
    principal in resource.repo.admins &&
    resource.env == "production" &&
    !resource.repo.isArchived
};
