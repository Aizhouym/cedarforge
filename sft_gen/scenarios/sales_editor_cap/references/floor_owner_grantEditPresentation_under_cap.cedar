permit (
    principal is User,
    action == Action::"grantEditAccessToPresentation",
    resource is Presentation
) when {
    principal == resource.owner &&
    resource.editorCount < resource.maxEditors &&
    context.target.job == Job::"internal"
};
