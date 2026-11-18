import unittest

from rules.validate_household_count import validate_household_count


class HouseholdTests(unittest.TestCase):
    def test_comparison_and_count_type(self):
        for value, expected in [(0, True), (2, True), (3, False), (-1, False),
                                (True, False), (1.5, False), ("1", False)]:
            self.assertEqual(validate_household_count(value, {"household_size": 2})[0], expected)

    def test_validate_available_count_before_household_size_arrives(self):
        self.assertTrue(validate_household_count(1, {})[0])
