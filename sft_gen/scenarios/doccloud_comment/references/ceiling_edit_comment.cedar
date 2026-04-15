permit (
    principal is User,
    action == Action::"EditComment",
    resource is Comment
)
when { principal == resource.author };
