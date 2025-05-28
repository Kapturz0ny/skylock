"""
Module to test the ResourceVisibility enum class.
"""

import unittest
from skylock_cli.model.resource_visibility import ResourceVisibility


class TestResourceVisibility(unittest.TestCase):
    """
    Test cases for the ResourceVisibility enum class.
    """

    def test_private_label(self):
        """
        Test the label of the PRIVATE visibility.
        """
        self.assertEqual(ResourceVisibility.PRIVATE.label, "private 🔐")

    def test_private_color(self):
        """
        Test the color of the PRIVATE visibility.
        """
        self.assertEqual(ResourceVisibility.PRIVATE.color, "red")

    def test_public_label(self):
        """
        Test the label of the PUBLIC visibility.
        """
        self.assertEqual(ResourceVisibility.PUBLIC.label, "public 🔓")

    def test_public_color(self):
        """
        Test the color of the PUBLIC visibility.
        """
        self.assertEqual(ResourceVisibility.PUBLIC.color, "green")

    def test_protected_label(self):
        """
        Test the label of the PROTECTED visibility.
        """
        self.assertEqual(ResourceVisibility.PROTECTED.label, "protected 🔐/🔒")

    def test_protected_color(self):
        """
        Test the color of the PROTECTED visibility.
        """
        self.assertEqual(ResourceVisibility.PROTECTED.color, "yellow")



if __name__ == "__main__":
    unittest.main()
