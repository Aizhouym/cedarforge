permit (
    principal is User,
    action == Action::"create",
    resource is Prescription
) when {
    principal.role == "physician"
};

permit (
    principal is User,
    action == Action::"review",
    resource is Prescription
) when {
    (principal.role == "pharmacist") ||
    (principal.role == "physician" && principal == resource.prescriber) ||
    (principal.role == "patient" && principal == resource.patient)
};

permit (
    principal is User,
    action == Action::"fill",
    resource is Prescription
) when {
    principal.role == "pharmacist" &&
    !resource.isFilled &&
    (!resource.isControlled ||
     (context has controlledSubstanceVerified && context.controlledSubstanceVerified))
};

permit (
    principal is User,
    action == Action::"viewHistory",
    resource is Prescription
) when {
    (principal.role == "patient" && principal == resource.patient) ||
    (principal.role == "physician" && principal == resource.prescriber) ||
    (principal.role == "nurse")
};