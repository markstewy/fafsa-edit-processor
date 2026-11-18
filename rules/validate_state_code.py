STATES = (
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO "
    "MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY"
).split()


def validate_state_code(value, params):
    if value not in STATES:
        return False, "Enter a two-letter US state abbreviation in uppercase."
    return True, ""
