permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
) when {
    !resource.isEarlyAccess &&
    !principal.profile.isKid &&
    resource.contentRating == "R"
};
