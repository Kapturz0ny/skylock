"""Resource model"""
from typing import Literal
from pydantic import BaseModel, PrivateAttr
from skylock_cli.model.resource_visibility import ResourceVisibility


class Resource(BaseModel):
    """Base class for resources"""

    _privacy: Literal["private", "protected", "public"] = PrivateAttr("private")
    _visibility: ResourceVisibility = PrivateAttr(ResourceVisibility.PRIVATE)

    def __init__(self, **data):
        """Custom initialization to handle is_public logic"""
        super().__init__(**data)
        match data.get("privacy"):
            case "public": self.make_public()
            case "protected": self.make_protected()
            case "private": self.make_private()

    def make_public(self):
        """Make the resource public"""
        self._privacy = "public"
        self._visibility = ResourceVisibility.PUBLIC

    def make_private(self):
        """Make the resource private"""
        self._privacy = "private"
        self._visibility = ResourceVisibility.PRIVATE

    def make_protected(self):
        """Make the resource protected"""
        self._privacy = "protected"
        self._visibility = ResourceVisibility.PROTECTED

    @property
    def privacy(self) -> Literal["private", "protected", "public"]:
        """Get whether the resource's privacy"""
        return self._privacy

    @property
    def visibility_label(self) -> str:
        """Get the visibility label"""
        return self._visibility.label

    @property
    def visibility_color(self) -> str:
        """Get the visibility color"""
        return self._visibility.color
