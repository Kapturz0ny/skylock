"""
Module with Private enum class
"""

from enum import Enum


class Privacy(str, Enum):
    """The class representing privacy."""
    PRIVATE = "private"
    PROTECTED = "protected"
    PUBLIC = "public"
