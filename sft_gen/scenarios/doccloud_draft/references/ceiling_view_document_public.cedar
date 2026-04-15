permit (
    principal is Public,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    !resource.isDraft &&
    (resource.publicAccess == "view" || resource.publicAccess == "edit")
};
