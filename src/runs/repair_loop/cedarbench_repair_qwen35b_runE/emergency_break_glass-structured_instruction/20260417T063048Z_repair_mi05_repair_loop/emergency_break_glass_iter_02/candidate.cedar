permit (
    principal is Clinician,
    action == Action::"viewRecord",
    resource is Record
) when {
    principal.hospital == resource.hospital &&
    principal.careTeamPatients.contains(resource.patient)
};

permit (
    principal is Clinician,
    action == Action::"viewRecord",
    resource is Record
) when {
    principal.hospital == resource.hospital &&
    !principal.careTeamPatients.contains(resource.patient) &&
    principal.isOnCall &&
    context.emergencyActive &&
    context.emergencyReason != ""
};

permit (
    principal is Clinician,
    action == Action::"editRecord",
    resource is Record
) when {
    principal.hospital == resource.hospital &&
    principal.careTeamPatients.contains(resource.patient)
};