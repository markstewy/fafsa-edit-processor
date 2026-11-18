def validate_household_count(value, params):
    if type(value) is not int or value < 0:
        return False, "Enter a non-negative whole number."
    household_size = params.get("household_size")
    if type(household_size) is int and household_size >= 0 and value > household_size:
        return False, "Number in college cannot exceed number in household."
    return True, ""
