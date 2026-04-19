permit (
    principal is Professional,
    action == Action::"viewDocument",
    resource is Document
) when {
    principal.assigned_orgs.contains({
        organization: resource.owner.organization,
        serviceline: resource.serviceline,
        location: resource.location
    })
};

permit (
    principal is Professional,
    action == Action::"viewClientProfile",
    resource is Client
) when {
    principal.assigned_orgs.contains({
        organization: resource.organization,
        serviceline: "",
        location: ""
    })
};

forbid (
    principal is Professional,
    action == Action::"viewDocument",
    resource is Document
) unless {
    context.consent.client == resource.owner &&
    context.consent.team_region_list.contains(principal.location)
};