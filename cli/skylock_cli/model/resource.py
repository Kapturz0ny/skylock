"""Resource model"""

from pydantic import BaseModel, PrivateAttr
from skylock_cli.model.resource_visibility import ResourceVisibility
from skylock_cli.model.privacy import Privacy


class Resource(BaseModel):
    """Base class for resources"""

    _privacy: Privacy = PrivateAttr(Privacy.PRIVATE)
    _visibility: ResourceVisibility = PrivateAttr(ResourceVisibility.PRIVATE)

    def __init__(self, **data):
        """Custom initialization to handle privacy logic"""
        super().__init__(**data)
        match data.get("privacy"):
            case Privacy.PUBLIC:
                self.make_public()
            case Privacy.PROTECTED:
                self.make_protected()
            case Privacy.PRIVATE:
                self.make_private()

    def make_public(self):
        """Make the resource public"""
        self._privacy = Privacy.PUBLIC
        self._visibility = ResourceVisibility.PUBLIC

    def make_private(self):
        """Make the resource private"""
        self._privacy = Privacy.PRIVATE
        self._visibility = ResourceVisibility.PRIVATE

    def make_protected(self):
        """Make the resource protected"""
        self._privacy = Privacy.PROTECTED
        self._visibility = ResourceVisibility.PROTECTED

    @property
    def privacy(self) -> Privacy:
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
