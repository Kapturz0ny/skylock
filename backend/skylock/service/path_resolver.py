from skylock.database.repository import FileRepository, FolderRepository, UserRepository
from skylock.database import models as db_models
from skylock.utils.exceptions import ResourceNotFoundException
from skylock.utils.path import UserPath


class PathResolver:
    """Resolves string paths to database entities and vice-versa."""

    def __init__(
        self,
        file_repository: FileRepository,
        folder_repository: FolderRepository,
        user_repository: UserRepository,
    ):
        """Initializes the PathResolver.

        Args:
            file_repository (FileRepository): Repository for file operations.
            folder_repository (FolderRepository): Repository for folder operations.
            user_repository (UserRepository): Repository for user operations.
        """
        self._file_repository = file_repository
        self._folder_repository = folder_repository
        self._user_repository = user_repository

    def folder_from_path(self, user_path: UserPath) -> db_models.FolderEntity:
        """Retrieves a folder entity from a given user path.

        Args:
            user_path (UserPath): The user-specific path to the folder.

        Returns:
            db_models.FolderEntity: The resolved folder entity.

        Raises:
            LookupError: If the root folder specified in the path does not exist.
            ResourceNotFoundException: If any part of the path does not resolve to a folder.
        """
        current_folder = self._get_root_folder(user_path.root_folder_name)

        if current_folder is None:
            raise LookupError(f"Root folder: {user_path.root_folder_name} does not exist")

        for folder_name in user_path.parts:
            current_folder = self._folder_repository.get_by_name_and_parent_id(
                folder_name, current_folder.id
            )
            if current_folder is None:
                raise ResourceNotFoundException(missing_resource_name=folder_name)

        return current_folder

    def file_from_path(self, user_path: UserPath) -> db_models.FileEntity:
        """Retrieves a file entity from a given user path.

        Args:
            user_path (UserPath): The user-specific path to the file.

        Returns:
            db_models.FileEntity: The resolved file entity.

        Raises:
            ResourceNotFoundException: If the parent folder or the file itself does not exist.
        """
        parent_folder = self.folder_from_path(user_path.parent)
        file = self._file_repository.get_by_name_and_parent(
            name=user_path.name, parent=parent_folder
        )

        if file is None:
            raise ResourceNotFoundException(missing_resource_name=user_path.name)

        return file

    def path_from_folder(self, folder: db_models.FolderEntity) -> UserPath:
        """Constructs a UserPath object from a folder entity.

        Args:
            folder (db_models.FolderEntity): The folder entity.

        Returns:
            UserPath: The corresponding user path.

        Raises:
            LookupError: If the owner (user) of the root folder cannot be found.
        """
        path_parts: list[str] = []
        current_folder = folder
        while current_folder.parent_folder is not None:
            path_parts.insert(0, current_folder.name)
            current_folder = current_folder.parent_folder
        owner = self._user_repository.get_by_id(current_folder.name)

        if owner is None:
            raise LookupError(f"User for root folder not found, id: {current_folder.name}")

        path = "/".join(path_parts)

        return UserPath(path=path, owner=owner)

    def path_from_file(self, file: db_models.FileEntity) -> UserPath:
        """Constructs a UserPath object from a file entity.

        Args:
            file (db_models.FileEntity): The file entity.

        Returns:
            UserPath: The corresponding user path.
        """
        parent_folder = file.folder
        parent_path = self.path_from_folder(parent_folder)
        return parent_path / file.name

    def path_from_link(self, link: db_models.LinkEntity) -> UserPath:
        """Constructs a UserPath object from a link entity.

        Args:
            link (db_models.LinkEntity): The link entity.

        Returns:
            UserPath: The corresponding user path.
        """
        parent_folder = link.folder
        parent_path = self.path_from_folder(parent_folder)
        return parent_path / link.name

    def _get_root_folder(self, name: str) -> db_models.FolderEntity | None:
        """Retrieves a root folder by its name.

        A root folder is identified by having no parent.

        Args:
            name (str): The name of the root folder (typically user's ID).

        Returns:
            db_models.FolderEntity | None: The root folder entity if found, else None.
        """
        return self._folder_repository.get_by_name_and_parent_id(name=name, parent_id=None)
