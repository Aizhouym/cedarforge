permit (
    principal is User,
    action == Action::"add_reader",
    resource is Repository
)
when {
    (principal in resource.admins || principal in resource.teamAdmins) &&
    !resource.isArchived
};
