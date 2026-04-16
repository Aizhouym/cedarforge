permit (
    principal is User,
    action == Action::"viewReport",
    resource is Report
)
when {
    principal in Role::"Role-A" &&
    principal.allowedTagsForRole has "Role-A" &&
    (
        !(principal.allowedTagsForRole["Role-A"] has production_status)
        || !(resource.workspace.tags has production_status)
        || (principal.allowedTagsForRole["Role-A"] has production_status && principal.allowedTagsForRole["Role-A"]["production_status"].contains("ALL"))
        || (resource.workspace.tags has production_status && resource.workspace.tags["production_status"].contains("ALL"))
        || (principal.allowedTagsForRole["Role-A"] has production_status && resource.workspace.tags has production_status && principal.allowedTagsForRole["Role-A"]["production_status"].containsAll(resource.workspace.tags["production_status"]))
    ) &&
    (
        !(principal.allowedTagsForRole["Role-A"] has country)
        || !(resource.workspace.tags has country)
        || (principal.allowedTagsForRole["Role-A"] has country && principal.allowedTagsForRole["Role-A"]["country"].contains("ALL"))
        || (resource.workspace.tags has country && resource.workspace.tags["country"].contains("ALL"))
        || (principal.allowedTagsForRole["Role-A"] has country && resource.workspace.tags has country && principal.allowedTagsForRole["Role-A"]["country"].containsAll(resource.workspace.tags["country"]))
    ) &&
    (
        !(principal.allowedTagsForRole["Role-A"] has stage)
        || !(resource.workspace.tags has stage)
        || (principal.allowedTagsForRole["Role-A"] has stage && principal.allowedTagsForRole["Role-A"]["stage"].contains("ALL"))
        || (resource.workspace.tags has stage && resource.workspace.tags["stage"].contains("ALL"))
        || (principal.allowedTagsForRole["Role-A"] has stage && resource.workspace.tags has stage && principal.allowedTagsForRole["Role-A"]["stage"].containsAll(resource.workspace.tags["stage"]))
    )
};

permit (
    principal is User,
    action == Action::"viewReport",
    resource is Report
)
when {
    principal in Role::"Role-B" &&
    !resource.isConfidential &&
    principal.allowedTagsForRole has "Role-B" &&
    (
        !(principal.allowedTagsForRole["Role-B"] has production_status)
        || !(resource.workspace.tags has production_status)
        || (principal.allowedTagsForRole["Role-B"] has production_status && principal.allowedTagsForRole["Role-B"]["production_status"].contains("ALL"))
        || (resource.workspace.tags has production_status && resource.workspace.tags["production_status"].contains("ALL"))
        || (principal.allowedTagsForRole["Role-B"] has production_status && resource.workspace.tags has production_status && principal.allowedTagsForRole["Role-B"]["production_status"].containsAll(resource.workspace.tags["production_status"]))
    ) &&
    (
        !(principal.allowedTagsForRole["Role-B"] has country)
        || !(resource.workspace.tags has country)
        || (principal.allowedTagsForRole["Role-B"] has country && principal.allowedTagsForRole["Role-B"]["country"].contains("ALL"))
        || (resource.workspace.tags has country && resource.workspace.tags["country"].contains("ALL"))
        || (principal.allowedTagsForRole["Role-B"] has country && resource.workspace.tags has country && principal.allowedTagsForRole["Role-B"]["country"].containsAll(resource.workspace.tags["country"]))
    ) &&
    (
        !(principal.allowedTagsForRole["Role-B"] has stage)
        || !(resource.workspace.tags has stage)
        || (principal.allowedTagsForRole["Role-B"] has stage && principal.allowedTagsForRole["Role-B"]["stage"].contains("ALL"))
        || (resource.workspace.tags has stage && resource.workspace.tags["stage"].contains("ALL"))
        || (principal.allowedTagsForRole["Role-B"] has stage && resource.workspace.tags has stage && principal.allowedTagsForRole["Role-B"]["stage"].containsAll(resource.workspace.tags["stage"]))
    )
};
