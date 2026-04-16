permit (
    principal is User,
    action == Action::"grantViewAccessToTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    (
        principal.job == Job::"internal" &&
        (
            principal in resource.editors ||
            principal in resource.editorMarkets
        )
    )
};
