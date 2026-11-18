import unittest

from rules.validate_ssn_format import validate_ssn_format


class SSNChecksTest(unittest.TestCase):
    def test_accepted_formats(self):
        for value in ["123456789", " 123-45-6789 "]:
            self.assertEqual(validate_ssn_format(value), (True, ""))

    def test_malformed(self):
        for value in ["123-456789", "12345-6789", "12345678", "1234567890",
                      "12345678a", "１２３４５６７８９"]:
            with self.subTest(value=value):
                self.assertEqual(validate_ssn_format(value),
                                 (False, "Must be a valid 9-digit Social Security Number."))

    def test_zero_blocks(self):
        for value in [" 000-12-3456 ", "123004567", "123-45-0000"]:
            self.assertEqual(validate_ssn_format(value), (False, "Invalid Social Security Number sequence."))

    def test_non_string(self):
        self.assertEqual(validate_ssn_format(123456789), (False, "Must be a string."))
