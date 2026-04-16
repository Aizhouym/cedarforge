permit (
    principal is User,
    action == Action::"delete_release",
    resource is Release
)
when {
    principal in resource.repo.admins &&
    principal != resource.author
};
