permit (
    principal is User,
    action == Action::"AddToShareACL",
    resource is Document
)
when { context.is_authenticated && context.userOrg != resource.ownerOrg && principal in resource.manageACL };
