permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
) when {
    resource.isFree &&
    (
        !(resource has availableFrom) ||
        (resource has availableFrom && context.now.datetime >= resource.availableFrom)
    )
};
