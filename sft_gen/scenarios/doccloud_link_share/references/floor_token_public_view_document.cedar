permit (
    principal is Public,
    action == Action::"ViewDocument",
    resource is Document
)
when { context.providedToken == resource.shareToken };
