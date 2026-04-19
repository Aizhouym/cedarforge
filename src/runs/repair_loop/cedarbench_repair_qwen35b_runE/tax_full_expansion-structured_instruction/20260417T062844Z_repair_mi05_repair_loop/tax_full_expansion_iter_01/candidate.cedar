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
    action == Action::"editDocument",
    resource is Document
) when {
    principal.assigned_orgs.contains({
        organization: resource.owner.organization,
        serviceline: resource.serviceline,
        location: resource.location
    })
};

permit (
    principal is Supervisor,
    action == Action::"viewDocument",
    resource is Document
) when {
    principal.supervised_orgs.contains(resource.owner.organization)
};

permit (
    principal is Supervisor,
    action == Action::"editDocument",
    resource is Document
) when {
    principal.supervised_orgs.contains(resource.owner.organization)
};

permit (
    principal is Auditor,
    action == Action::"viewDocument",
    resource is Document
) when {
    principal.auditScope.contains(resource.serviceline)
};

forbid (
    principal is Professional,
    action == Action::"viewDocument",
    resource is Document
) unless {
    context.consent.client == resource.owner &&
    context.consent.team_region_list.contains(principal.location)
};

forbid (
    principal is Professional,
    action == Action::"editDocument",
    resource is Document
) unless {
    context.consent.client == resource.owner &&
    context.consent.team_region_list.contains(principal.location)
};

forbid (
    principal is Supervisor,
    action == Action::"viewDocument",
    resource is Document
) unless {
    context.consent.client == resource.owner &&
    context.consent.team_region_list.contains(principal.location)
};

forbid (
    principal is Supervisor,
    action == Action::"editDocument",
    resource is Document
) unless {
    context.consent.client == resource.owner &&
    context.consent.team_region_list.contains(principal.location)
};

forbid (
    principal is Auditor,
    action == Action::"viewDocument",
    resource is Document
) unless {
    context.consent.client == resource.owner &&
    context.consent.team_region_list.contains(principal.location)
};

forbid (
    principal is Professional,
    action == Action::"viewDocument",
    resource is Document
) when {
    resource.isSensitive
} unless {
    context.consent.team_region_list.contains("HQ")
};

forbid (
    principal is Professional,
    action == Action::"editDocument",
    resource is Document
) when {
    resource.isSensitive
} unless {
    context.consent.team_region_list.contains("HQ")
};

forbid (
    principal is Supervisor,
    action == Action::"viewDocument",
    resource is Document
) when {
    resource.isSensitive
} unless {
    context.consent.team_region_list.contains("HQ")
};

forbid (
    principal is Supervisor,
    action == Action::"editDocument",
    resource is Document
) when {
    resource.isSensitive
} unless {
    context.consent.team_region_list.contains("HQ")
};

forbid (
    principal is Auditor,
    action == Action::"viewDocument",
    resource is Document
) when {
    resource.isSensitive
} unless {
    context.consent.team_region_list.contains("HQ")
};