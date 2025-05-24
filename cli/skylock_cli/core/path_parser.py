"""This module contains the function to parse the user input path"""

from pathlib import Path


def parse_path(cwd: Path, user_input_path: Path) -> Path:
    """
    Parse the user input path and return the absolute path
    """
    user_input_path = Path(str(user_input_path).replace("~/", "/"))

    if user_input_path.is_absolute():
        return user_input_path
    return (cwd / user_input_path).resolve()


def is_directory(path: str) -> bool:
    """
    Check if the path is a directory
    """
    return path.endswith("/")
