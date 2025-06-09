"""
Module to test the File model.
"""

import unittest
from pathlib import Path
from typer.colors import YELLOW
from skylock_cli.model.file import File
from skylock_cli.model.privacy import Privacy


class TestFile(unittest.TestCase):
    """
    Test cases for the File model.
    """

    def test_file_creation(self):
        """
        Test the creation of a File instance.
        """
        file = File(name="example.txt", path=Path("/home/user/example.txt"), size=10)
        self.assertEqual(file.name, "example.txt")
        self.assertEqual(file.path, Path("/home/user/example.txt"))
        self.assertEqual(file.color, YELLOW)
        self.assertEqual(file.privacy, Privacy.PRIVATE)
        self.assertEqual(file.type_label, "file")

    def test_file_default_color(self):
        """
        Test the default color of a File instance.
        """
        file = File(name="example.txt", path=Path("/home/user/example.txt"), size=10)
        self.assertEqual(file.color, YELLOW)

    def test_file_custom_color(self):
        """
        Test setting a custom color for a File instance.
        """
        custom_color = "blue"
        file = File(
            name="example.txt", path=Path("/home/user/example.txt"), color=custom_color, size=10
        )
        self.assertEqual(file.color, custom_color)


if __name__ == "__main__":
    unittest.main()
