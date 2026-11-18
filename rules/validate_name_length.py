def validate_name_length(value: object, params: dict) -> tuple[bool, str]:
    """Check the trimmed string length against inclusive bounds."""
    if not isinstance(value, str):
        return False, "Must be a string."

    minimum = params.get("min", 0)
    maximum = params.get("max")
    length = len(value.strip())
    if length < minimum or (maximum is not None and length > maximum):
        if maximum is None:
            return False, f"Length must be at least {minimum} characters."
        return False, f"Length must be between {minimum} and {maximum} characters."
    return True, ""
