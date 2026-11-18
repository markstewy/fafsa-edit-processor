import re


def validate_ssn_format(value: object, params=None) -> tuple[bool, str]:
    """Accept nine ASCII digits, optionally grouped as XXX-XX-XXXX."""
    if not isinstance(value, str):
        return False, "Must be a string."

    match = re.fullmatch(r"([0-9]{3})(-?)([0-9]{2})\2([0-9]{4})", value.strip())
    if match is None:
        return False, "Must be a valid 9-digit Social Security Number."
    area, _, group, serial = match.groups()
    if area == "000" or group == "00" or serial == "0000":
        return False, "Invalid Social Security Number sequence."
    return True, ""
