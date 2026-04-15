permit (
    principal is Public,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    !(context.now > resource.expiresAt) &&
    resource.publicAccess == "view"
};
