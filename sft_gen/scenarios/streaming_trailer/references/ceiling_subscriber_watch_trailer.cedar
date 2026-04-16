permit (
    principal is Subscriber,
    action == Action::"watch_trailer",
    resource is Trailer
)
when {
    true
};
