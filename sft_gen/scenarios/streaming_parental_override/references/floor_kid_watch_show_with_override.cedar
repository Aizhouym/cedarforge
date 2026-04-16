permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    context.now.datetime >= resource.releaseDate &&
    principal.profile.isKid &&
    context.parentalOverride
};
