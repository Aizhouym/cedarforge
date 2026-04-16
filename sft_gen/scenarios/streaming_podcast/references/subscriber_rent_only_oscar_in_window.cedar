permit (
    principal is Subscriber,
    action == Action::"rent",
    resource is Movie
) when {
    resource.isOscarNominated &&
    context.now.datetime >= datetime("2025-02-02T00:00:00Z") &&
    context.now.datetime <= datetime("2025-03-02T23:59:59Z")
};
