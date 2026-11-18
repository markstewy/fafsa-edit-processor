def validate_choice(value, params):
    choices = params["choices"]
    if value not in choices:
        return False, f"Choose one of {', '.join(choices)}."
    return True, ""
