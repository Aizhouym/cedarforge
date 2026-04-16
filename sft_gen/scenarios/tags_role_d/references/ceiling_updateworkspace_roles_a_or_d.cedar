permit (
    principal is User,
    action == Action::"UpdateWorkspace",
    resource is Workspace
) when {
    (
        principal in Role::"Role-A" &&
        principal.allowedTagsForRole has "Role-A" &&
        (
            !(resource.tags has production_status) ||
            !(principal.allowedTagsForRole has "Role-A" && principal.allowedTagsForRole["Role-A"] has production_status) ||
            (
                principal.allowedTagsForRole has "Role-A" &&
                principal.allowedTagsForRole["Role-A"] has production_status &&
                (
                    principal.allowedTagsForRole["Role-A"].production_status.contains("ALL") ||
                    (resource.tags has production_status && resource.tags.production_status.contains("ALL")) ||
                    (resource.tags has production_status && principal.allowedTagsForRole["Role-A"].production_status.containsAll(resource.tags.production_status))
                )
            )
        ) &&
        (
            !(resource.tags has country) ||
            !(principal.allowedTagsForRole has "Role-A" && principal.allowedTagsForRole["Role-A"] has country) ||
            (
                principal.allowedTagsForRole has "Role-A" &&
                principal.allowedTagsForRole["Role-A"] has country &&
                (
                    principal.allowedTagsForRole["Role-A"].country.contains("ALL") ||
                    (resource.tags has country && resource.tags.country.contains("ALL")) ||
                    (resource.tags has country && principal.allowedTagsForRole["Role-A"].country.containsAll(resource.tags.country))
                )
            )
        ) &&
        (
            !(resource.tags has stage) ||
            !(principal.allowedTagsForRole has "Role-A" && principal.allowedTagsForRole["Role-A"] has stage) ||
            (
                principal.allowedTagsForRole has "Role-A" &&
                principal.allowedTagsForRole["Role-A"] has stage &&
                (
                    principal.allowedTagsForRole["Role-A"].stage.contains("ALL") ||
                    (resource.tags has stage && resource.tags.stage.contains("ALL")) ||
                    (resource.tags has stage && principal.allowedTagsForRole["Role-A"].stage.containsAll(resource.tags.stage))
                )
            )
        )
    ) ||
    (
        principal in Role::"Role-D" &&
        principal.allowedTagsForRole has "Role-D" &&
        (
            !(resource.tags has production_status) ||
            !(principal.allowedTagsForRole has "Role-D" && principal.allowedTagsForRole["Role-D"] has production_status) ||
            (
                principal.allowedTagsForRole has "Role-D" &&
                principal.allowedTagsForRole["Role-D"] has production_status &&
                (
                    principal.allowedTagsForRole["Role-D"].production_status.contains("ALL") ||
                    (resource.tags has production_status && resource.tags.production_status.contains("ALL")) ||
                    (resource.tags has production_status && principal.allowedTagsForRole["Role-D"].production_status.containsAll(resource.tags.production_status))
                )
            )
        ) &&
        (
            !(resource.tags has country) ||
            !(principal.allowedTagsForRole has "Role-D" && principal.allowedTagsForRole["Role-D"] has country) ||
            (
                principal.allowedTagsForRole has "Role-D" &&
                principal.allowedTagsForRole["Role-D"] has country &&
                (
                    principal.allowedTagsForRole["Role-D"].country.contains("ALL") ||
                    (resource.tags has country && resource.tags.country.contains("ALL")) ||
                    (resource.tags has country && principal.allowedTagsForRole["Role-D"].country.containsAll(resource.tags.country))
                )
            )
        ) &&
        (
            !(resource.tags has stage) ||
            !(principal.allowedTagsForRole has "Role-D" && principal.allowedTagsForRole["Role-D"] has stage) ||
            (
                principal.allowedTagsForRole has "Role-D" &&
                principal.allowedTagsForRole["Role-D"] has stage &&
                (
                    principal.allowedTagsForRole["Role-D"].stage.contains("ALL") ||
                    (resource.tags has stage && resource.tags.stage.contains("ALL")) ||
                    (resource.tags has stage && principal.allowedTagsForRole["Role-D"].stage.containsAll(resource.tags.stage))
                )
            )
        )
    )
};
