permit (
    principal is User,
    action == Action::"EditIsPrivate",
    resource is Document
)
when { context.is_authenticated && !resource.isDraft && principal in resource.manageACL };
