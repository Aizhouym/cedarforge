permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
) when {
    resource.isFree &&
    resource.contentRating != "NC-17"
};
