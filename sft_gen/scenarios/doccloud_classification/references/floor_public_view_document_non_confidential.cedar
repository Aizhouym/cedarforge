permit (
    principal is Public,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    resource.classification != "confidential" &&
    resource.publicAccess == "view"
};
