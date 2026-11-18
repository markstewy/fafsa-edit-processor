"""Stage definitions and transitions for cumulative FAFSA submissions."""

BASE_FIELDS = [
    "studentInfo.firstName", "studentInfo.lastName", "studentInfo.dateOfBirth",
    "studentInfo.ssn", "income.studentIncome", "household.numberInHousehold",
    "household.numberInCollege", "stateOfResidence",
]
PARENT_FIELDS = ["income.parentIncome"]
SPOUSE_FIELDS = ["spouseInfo.firstName", "spouseInfo.lastName", "spouseInfo.ssn"]


def application_stage(payload):
    return f"stage_{payload['dependencyStatus']}_{payload['maritalStatus']}"


# Each stage enforces its required fields in the order listed.
STAGE_GRAPH = {
    "root_stage": "stage_statuses",
    "stages": {
        "stage_statuses": {
            "required_fields": ["dependencyStatus", "maritalStatus"],
            "transition": application_stage,
        },
        "stage_independent_single": {"required_fields": BASE_FIELDS},
        "stage_dependent_single": {"required_fields": BASE_FIELDS + PARENT_FIELDS},
        "stage_independent_married": {"required_fields": BASE_FIELDS + SPOUSE_FIELDS},
        "stage_dependent_married": {"required_fields": BASE_FIELDS + PARENT_FIELDS + SPOUSE_FIELDS},
    },
}
