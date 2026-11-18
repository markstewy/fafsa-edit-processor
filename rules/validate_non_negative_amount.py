from decimal import Decimal, InvalidOperation


def validate_non_negative_amount(value: object, params=None) -> tuple[bool, str]:
    """Accept finite, non-negative amounts, including numeric strings."""
    try:
        amount = Decimal(str(value))
    except InvalidOperation:
        return False, "Must be a valid numeric value."
    if not amount.is_finite():
        return False, "Must be a valid numeric value."
    if amount < 0:
        return False, "Amount cannot be negative."
    return True, ""
