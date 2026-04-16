
// --- Verified and appended ---
permit (
    principal is User,
    action in [Action::"pull", Action::"fork"],
    resource is Repository
)
when { principal in resource.readers };

permit (
    principal is User,
    action == Action::"push",
    resource is Repository
)
when { principal in resource.writers && !resource.isArchived };

permit (
    principal is User,
    action == Action::"edit_issue",
    resource is Issue
)
when {
    (principal in resource.repo.readers && principal == resource.reporter) ||
    principal in resource.repo.writers
};

permit (
    principal is User,
    action == Action::"delete_issue",
    resource is Issue
)
when {
    (principal in resource.repo.readers && principal == resource.reporter) ||
    principal in resource.repo.maintainers
};

permit (
    principal is User,
    action == Action::"assign_issue",
    resource is Issue
)
when { principal in resource.repo.triagers };

permit (
    principal is User,
    action in [
        Action::"add_reader",
        Action::"add_writer",
        Action::"add_maintainer",
        Action::"add_admin",
        Action::"add_triager"
    ],
    resource is Repository
)
when { principal in resource.admins && !resource.isArchived };

permit (
    principal is User,
    action == Action::"create_release",
    resource is Release
)
when {
    principal in resource.repo.maintainers ||
    principal in resource.repo.admins
};

permit (
    principal is User,
    action == Action::"delete_release",
    resource is Release
)
when {
    principal in resource.repo.maintainers ||
    principal in resource.repo.admins
};

forbid (
    principal is User,
    action == Action::"delete_release",
    resource is Release
)
when { principal == resource.author };
