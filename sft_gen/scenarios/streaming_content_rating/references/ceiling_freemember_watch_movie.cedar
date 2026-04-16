permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
) when {
    resource.isFree &&
    resource.contentRating != "NC-17"
};
