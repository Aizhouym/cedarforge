permit (
    principal is User,
    action == Action::"DeleteComment",
    resource is Comment
)
when { principal in resource.document.manageACL };
