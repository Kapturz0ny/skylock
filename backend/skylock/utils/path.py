import pathlib


from skylock.database.models import UserEntity
from skylock.utils.exceptions import ForbiddenActionException, InvalidPathException


class UserPath:
    def __init__(self, path: str, owner: UserEntity):
        self._parsed_path = self._validate_and_parse_path(path)
        self._owner = owner

    @classmethod
    def root_folder_of(cls, owner: UserEntity) -> "UserPath":
        return cls(path="", owner=owner)

    @property
    def path(self) -> str:
        if self.is_root_folder():
            return ""
        return str(self._parsed_path)

    @property
    def owner(self) -> UserEntity:
        return self._owner

    @property
    def root_folder_name(self) -> str:
        return self._owner.id

    @property
    def parts(self) -> tuple[str, ...]:
        return self._parsed_path.parts

    @property
    def parent(self) -> "UserPath":
        if self.is_root_folder():
            raise ForbiddenActionException("You cannot access parent of root folder")
        return UserPath(path=str(self._parsed_path.parent), owner=self._owner)

    @property
    def parents(self) -> tuple["UserPath", ...]:
        if self.is_root_folder():
            raise ForbiddenActionException("You cannot access parent of root folder")
        return tuple(
            UserPath(path=str(parent), owner=self._owner) for parent in self._parsed_path.parents
        )

    @property
    def name(self) -> str:
        return str(self._parsed_path.name)

    def is_root_folder(self):
        return self._parsed_path == pathlib.PurePosixPath("")

    def _validate_and_parse_path(self, initial_path: str) -> pathlib.PurePosixPath:
        max_length = 255
        if len(str(initial_path)) > max_length:
            raise InvalidPathException("Path length exceeds allowed maximum.")

        parsed_path = pathlib.PurePosixPath(initial_path)

        if parsed_path.is_absolute():
            parsed_path = parsed_path.relative_to(parsed_path.root)

        return parsed_path

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UserPath):
            return NotImplemented
        return self.owner == other.owner and self.path == other.path

    def __truediv__(self, other: object) -> "UserPath":
        if not isinstance(other, str):
            return NotImplemented
        current_path = self.path
        new_path = current_path + "/" + other.strip("/")
        return UserPath(path=new_path, owner=self.owner)
