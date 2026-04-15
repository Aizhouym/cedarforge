permit (
    principal is User,
    action == Action::"DeleteDocument",
    resource is Document
)
when { context.is_authenticated && !resource.isDraft && principal in resource.manageACL };
