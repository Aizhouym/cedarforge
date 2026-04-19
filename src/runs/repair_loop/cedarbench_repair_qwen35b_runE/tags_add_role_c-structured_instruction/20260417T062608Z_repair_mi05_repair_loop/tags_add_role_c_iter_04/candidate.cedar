permit (
    principal is User,
    action == Action::"UpdateWorkspace",
    resource is Workspace
) when {
    principal in Role::"Role-A" &&
    tagMatch(principal, resource, "Role-A")
};

permit (
    principal is User,
    action == Action::"DeleteWorkspace",
    resource is Workspace
) when {
    principal in Role::"Role-A" &&
    tagMatch(principal, resource, "Role-A")
};

permit (
    principal is User,
    action == Action::"ReadWorkspace",
    resource is Workspace
) when {
    (principal in Role::"Role-A" && tagMatch(principal, resource, "Role-A")) ||
    (principal in Role::"Role-B" && tagMatch(principal, resource, "Role-B"))
};

permit (
    principal is User,
    action == Action::"ArchiveWorkspace",
    resource is Workspace
) when {
    principal in Role::"Role-C" &&
    tagMatch(principal, resource, "Role-C")
};

fn tagMatch(
    principal: User,
    resource: Workspace,
    role: String
) -> Bool {
    let userTags = principal.allowedTagsForRole[role] ?? {};
    let workspaceTags = resource.tags;

    checkDimension(userTags, workspaceTags, "production_status") &&
    checkDimension(userTags, workspaceTags, "country") &&
    checkDimension(userTags, workspaceTags, "stage")
};

fn checkDimension(
    userTags: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
    workspaceTags: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
    dimension: String
) -> Bool {
    let userSet = userTags[dimension] ?? {};
    let workspaceSet = workspaceTags[dimension] ?? {};

    if (userSet.contains("ALL") || workspaceSet.contains("ALL")) {
        true
    } else if (userSet.isEmpty() || workspaceSet.isEmpty()) {
        true
    } else {
        userSet.containsAll(workspaceSet)
    }
};