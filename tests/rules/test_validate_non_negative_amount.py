import unittest
from decimal import Decimal

from rules.validate_non_negative_amount import validate_non_negative_amount


class NumericChecksTest(unittest.TestCase):
    def test_non_negative(self):
        for value in [0, 10, 1.25, " 2.50 ", Decimal("0.01")]:
            self.assertEqual(validate_non_negative_amount(value), (True, ""))

    def test_negative(self):
        for value in [-1, "-0.01", "-1e-500"]:
            self.assertEqual(validate_non_negative_amount(value), (False, "Amount cannot be negative."))

    def test_invalid_amount(self):
        for value in [None, True, "", "abc", float("nan"), "Infinity", "-Infinity"]:
            with self.subTest(value=value):
                self.assertEqual(validate_non_negative_amount(value), (False, "Must be a valid numeric value."))
