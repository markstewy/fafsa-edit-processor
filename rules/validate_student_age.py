from datetime import date


def validate_student_age(value, params):
    try:
        birth = date.fromisoformat(value)
        if birth.isoformat() != value:
            raise ValueError
    except (TypeError, ValueError):
        return False, "Enter a date of birth as YYYY-MM-DD."
    today = date.today()
    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    if age < 14:
        return False, "Student must be at least 14 years old."
    return True, ""
