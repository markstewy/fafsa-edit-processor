import unittest

from rules.validate_name_length import validate_name_length


class StringChecksTest(unittest.TestCase):
    def test_trimmed_length_includes_both_bounds(self):
        for value in [" a ", "abc"]:
            self.assertEqual(validate_name_length(value, {"min": 1, "max": 3}), (True, ""))

    def test_outside_bounds(self):
        for value in [" ", "abcd"]:
            self.assertEqual(validate_name_length(value, {"min": 1, "max": 3}),
                             (False, "Length must be between 1 and 3 characters."))

    def test_optional_bounds(self):
        self.assertEqual(validate_name_length("", {}), (True, ""))
        self.assertEqual(validate_name_length("", {"min": 2}),
                         (False, "Length must be at least 2 characters."))
        self.assertEqual(validate_name_length("x", {"max": 0})[0], False)

    def test_non_string(self):
        self.assertEqual(validate_name_length(None, {}), (False, "Must be a string."))
