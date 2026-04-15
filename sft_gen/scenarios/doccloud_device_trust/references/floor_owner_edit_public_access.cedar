permit (
    principal is User,
    action == Action::"EditPublicAccess",
    resource is Document
)
when { context.is_authenticated && context.deviceTrusted && principal == resource.owner };
