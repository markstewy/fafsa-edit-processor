import unittest
from datetime import date, timedelta
from unittest.mock import patch

from rules.validate_student_age import validate_student_age


class AgeTests(unittest.TestCase):
    def test_birthday_boundary(self):
        with patch("rules.validate_student_age.date", wraps=date) as clock:
            clock.today.return_value = date(2026, 5, 15)
            birthday = date(2012, 5, 15)
            self.assertTrue(validate_student_age(birthday.isoformat(), {})[0])
            self.assertFalse(validate_student_age((birthday + timedelta(days=1)).isoformat(), {})[0])

    def test_invalid_dates(self):
        for value in ["2020-02-30", "20030515", None]:
            self.assertFalse(validate_student_age(value, {})[0])
