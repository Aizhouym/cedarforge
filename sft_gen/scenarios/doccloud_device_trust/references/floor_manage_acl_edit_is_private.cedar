permit (
    principal is User,
    action == Action::"EditIsPrivate",
    resource is Document
)
when { context.is_authenticated && context.deviceTrusted && principal in resource.manageACL };
