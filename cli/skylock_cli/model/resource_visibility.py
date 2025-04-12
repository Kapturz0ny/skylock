"""Module for the ResourceVisibility enum class."""

from enum import Enum


class ResourceVisibility(str, Enum):
    """
    Resource visibility enum class.

    Enum values are in the format "label,color" to make the ResourceVisibility object json serializable
    """

    PRIVATE = "private 🔐,red"
    PUBLIC = "public 🔓,green"
    PROTECTED = "protected 🔐/🔒,yellow"

    @property
    def label(self):
        """Get the visibility label."""
        return self.value.split(",")[0]

    @property
    def color(self):
        """Get the visibility color."""
        return self.value.split(",")[1]
    
