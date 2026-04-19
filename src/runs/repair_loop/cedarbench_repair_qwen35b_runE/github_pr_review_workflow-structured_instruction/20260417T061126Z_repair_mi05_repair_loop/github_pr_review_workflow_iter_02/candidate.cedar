permit (
    principal is User,
    action == Action::"pull",
    resource is Repository
) when {
    principal in resource.readers
};

permit (
    principal is User,
    action == Action::"fork",
    resource is Repository
) when {
    principal in resource.readers
};

permit (
    principal is User,
    action == Action::"push",
    resource is Repository
) when {
    principal in resource.writers &&
    !resource.isArchived
};

permit (
    principal is User,
    action == Action::"assign_issue",
    resource is Issue
) when {
    principal in resource.repo.triagers
};

permit (
    principal is User,
    action == Action::"edit_issue",
    resource is Issue
) when {
    (principal in resource.repo.writers) ||
    (principal in resource.repo.readers && principal == resource.reporter)
};

permit (
    principal is User,
    action == Action::"delete_issue",
    resource is Issue
) when {
    (principal in resource.repo.maintainers) ||
    (principal in resource.repo.readers && principal == resource.reporter)
};

permit (
    principal is User,
    action == Action::"add_reader",
    resource is Repository
) when {
    principal in resource.admins &&
    !resource.isArchived
};

permit (
    principal is User,
    action == Action::"add_writer",
    resource is Repository
) when {
    principal in resource.admins &&
    !resource.isArchived
};

permit (
    principal is User,
    action == Action::"add_maintainer",
    resource is Repository
) when {
    principal in resource.admins &&
    !resource.isArchived
};

permit (
    principal is User,
    action == Action::"add_admin",
    resource is Repository
) when {
    principal in resource.admins &&
    !resource.isArchived
};

permit (
    principal is User,
    action == Action::"add_triager",
    resource is Repository
) when {
    principal in resource.admins &&
    !resource.isArchived
};

permit (
    principal is User,
    action == Action::"merge_pr",
    resource is PullRequest
) when {
    (principal in resource.repo.writers) &&
    !resource.repo.isArchived
};

permit (
    principal is User,
    action == Action::"approve_pr",
    resource is PullRequest
) when {
    (principal in resource.repo.readers) &&
    (principal != resource.author)
};

permit (
    principal is User,
    action == Action::"request_changes",
    resource is PullRequest
) when {
    (principal in resource.repo.readers) &&
    (principal != resource.author)
};