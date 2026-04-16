permit (
    principal is Subscriber,
    action == Action::"download_podcast",
    resource is Podcast
) when {
    true
};
