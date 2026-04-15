permit (
    principal is User,
    action == Action::"DeleteComment",
    resource is Comment
)
when {
    principal == resource.author ||
    principal == resource.document.owner ||
    principal in resource.document.manageACL
};
