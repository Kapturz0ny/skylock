from typing import IO, Optional
from fastapi import HTTPException

from skylock.database import models as db_models
from skylock.database.repository import (
    FileRepository,
    FolderRepository,
    UserRepository,
    SharedFileRepository,
    LinkRepository,
)
from skylock.service.path_resolver import PathResolver
from skylock.utils.exceptions import (
    FolderNotEmptyException,
    ForbiddenActionException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    RootFolderAlreadyExistsException,
    UserNotFoundException,
)
from skylock.utils.path import UserPath
from skylock.utils.storage import FileStorageService

from skylock.api.models import Privacy, FolderType, ResourceType
from skylock.utils.security import get_user_from_jwt

from skylock.utils.logger import logger


class ResourceService:
    """Manages user resources like files, folders, and links."""

    def __init__(
        self,
        file_repository: FileRepository,
        folder_repository: FolderRepository,
        path_resolver: PathResolver,
        file_storage_service: FileStorageService,
        user_repository: UserRepository,
        shared_file_repository: SharedFileRepository,
        link_repository: LinkRepository,
    ):
        """Initializes the ResourceService with its dependencies.

        Args:
            file_repository: Repository for file data operations.
            folder_repository: Repository for folder data operations.
            path_resolver: Utility for resolving paths to entities.
            file_storage_service: Service for physical file storage.
            user_repository: Repository for user data operations.
            shared_file_repository: Repository for shared file records.
            link_repository: Repository for link data operations.
        """
        self._file_repository = file_repository
        self._folder_repository = folder_repository
        self._path_resolver = path_resolver
        self._file_storage_service = file_storage_service
        self._user_repository = user_repository
        self._shared_file_repository = shared_file_repository
        self._link_repository = link_repository

    def get_folder(self, user_path: UserPath) -> db_models.FolderEntity:
        """Retrieves a folder entity based on its user path.

        Args:
            user_path: The path to the folder.

        Returns:
            The folder entity.
        """
        return self._path_resolver.folder_from_path(user_path)

    def get_folder_by_id(self, folder_id: str) -> db_models.FolderEntity:
        """Retrieves a folder entity by its ID.

        Args:
            folder_id: The ID of the folder.

        Returns:
            The folder entity.

        Raises:
            ResourceNotFoundException: If the folder is not found.
        """
        current_folder = self._folder_repository.get_by_id(folder_id)

        if current_folder is None:
            raise ResourceNotFoundException(missing_resource_name=folder_id)

        return current_folder

    def get_public_folder(self, folder_id: str) -> db_models.FolderEntity:
        """Retrieves a folder by ID, ensuring it is public.

        Args:
            folder_id: The ID of the folder.

        Returns:
            The public folder entity.

        Raises:
            ResourceNotFoundException: If the folder is not found.
            ForbiddenActionException: If the folder is not public.
        """
        folder = self.get_folder_by_id(folder_id)

        if not folder.privacy == Privacy.PUBLIC:
            raise ForbiddenActionException(f"Folder with id {folder_id} is not public")

        return folder

    def create_folder(
        self,
        user_path: UserPath,
        privacy: Privacy = Privacy.PRIVATE,
        folder_type: FolderType = FolderType.NORMAL,
    ) -> db_models.FolderEntity:
        """Creates a new folder at the specified user path.

        Args:
            user_path: The path where the folder will be created.
            privacy: The privacy setting for the new folder.
            folder_type: The type of the new folder.

        Returns:
            The created folder entity.

        Raises:
            ForbiddenActionException: If attempting to create a root folder.
            ResourceAlreadyExistsException: If a resource with the same name exists.
        """
        if user_path.is_root_folder():
            raise ForbiddenActionException("Creation of root folder is forbidden")

        folder_name = user_path.name
        parent_path = user_path.parent
        parent = self._path_resolver.folder_from_path(parent_path)

        self._assert_no_children_matching_name(parent, folder_name)

        new_folder = db_models.FolderEntity(
            name=folder_name,
            parent_folder=parent,
            owner=user_path.owner,
            privacy=privacy,
            type=folder_type,
        )
        return self._folder_repository.save(new_folder)

    def update_folder(
        self, user_path: UserPath, privacy: Privacy, recursive: bool
    ) -> db_models.FolderEntity:
        """Updates the privacy of a folder and, optionally, its contents.

        Args:
            user_path: The path to the folder to update.
            privacy: The new privacy setting.
            recursive: If True, applies changes to subfolders and files.

        Returns:
            The updated folder entity.
        """
        folder = self._path_resolver.folder_from_path(user_path)
        self._update_folder(folder, privacy, recursive)
        return folder

    def _update_folder(
        self, folder: db_models.FolderEntity, privacy: Privacy, recursive: bool
    ) -> None:
        """Helper to update folder privacy recursively."""
        if folder.type == FolderType.SHARED or folder.type == FolderType.SHARING_USER:
            return
        
        folder.privacy = privacy

        for file in folder.files:
            self._update_file(file, privacy)

        if recursive:
            for subfolder in folder.subfolders:
                self._update_folder(subfolder, privacy, recursive)

        self._folder_repository.save(folder)

    def _update_file(self, file: db_models.FileEntity, privacy: Privacy) -> None:
        """Helper to update file privacy."""
        file.privacy = privacy
        self._file_repository.save(file)

    def create_folder_with_parents(
        self, user_path: UserPath, privacy: Privacy = Privacy.PRIVATE
    ) -> db_models.FolderEntity:
        """Creates a folder, including any non-existent parent folders.

        Args:
            user_path: The full path to the target folder.
            privacy: The privacy setting for newly created folders.

        Returns:
            The target created folder entity.
        """
        if user_path.is_root_folder():
            raise ForbiddenActionException("Creation of root folder is forbidden")

        for parent_user_path in reversed(user_path.parents):
            if not parent_user_path.is_root_folder() and not self._folder_exists(parent_user_path):
                self.create_folder(parent_user_path, privacy=privacy)

        return self.create_folder(user_path, privacy)

    def _folder_exists(self, user_path: UserPath) -> bool:
        """Checks if a folder exists at the given path."""
        try:
            self._path_resolver.folder_from_path(user_path)
            return True
        except ResourceNotFoundException:
            return False

    def delete_folder(self, user_path: UserPath, is_recursively: bool = False):
        """Deletes a folder.

        Args:
            user_path: The path to the folder to delete.
            is_recursively: If True, deletes non-empty folders.

        Raises:
            ForbiddenActionException: If trying to delete a root or special folder.
            FolderNotEmptyException: If folder is not empty and not recursive.
        """
        folder = self._path_resolver.folder_from_path(user_path)
        self._delete_folder(folder, is_recursively=is_recursively)

    def _delete_folder(self, folder: db_models.FolderEntity, is_recursively: bool = False):
        """Helper to delete folder and its contents."""
        if folder.is_root():
            raise ForbiddenActionException("Deletion of root folder is forbidden")

        if folder.type == FolderType.SHARED:
            logger.warning("Attempted to delete a special folder: %s", folder.name)
            raise ForbiddenActionException("You cannot delete special folders")

        has_folder_children = bool(folder.subfolders or folder.files or folder.links)
        if not is_recursively and has_folder_children:
            raise FolderNotEmptyException()

        for file in folder.files:
            self._delete_file(file)

        for subfolder in folder.subfolders:
            self._delete_folder(subfolder, is_recursively=True)

        if folder.type == FolderType.SHARING_USER:
            for link in folder.links:
                if link.target_file_id:  # safe check
                    self._shared_file_repository.delete_shared_files_from_users(
                        link.target_file_id, folder.owner.id
                    )
                self._link_repository.delete(link)
        else:
            for link in folder.links:
                self._link_repository.delete(link)

        self._folder_repository.delete(folder)

    def get_file(self, user_path: UserPath) -> db_models.FileEntity:
        """Retrieves a file entity based on its user path.

        Args:
            user_path: The path to the file.

        Returns:
            The file entity.
        """
        return self._path_resolver.file_from_path(user_path)

    def get_file_by_id(self, file_id: str) -> db_models.FileEntity:
        """Retrieves a file entity by its ID.

        Args:
            file_id: The ID of the file.

        Returns:
            The file entity.

        Raises:
            ResourceNotFoundException: If the file is not found.
        """
        file = self._file_repository.get_by_id(file_id)

        if file is None:
            raise ResourceNotFoundException(missing_resource_name=file_id)

        return file

    def get_verified_file(self, file_id: str, token: Optional[str]) -> db_models.FileEntity:
        """Retrieves a file by ID, performing access verification.

        Args:
            file_id: The ID of the file.
            token: The authentication token for access checks.

        Returns:
            The file entity if access is granted.

        Raises:
            ResourceNotFoundException: If file not found.
            ForbiddenActionException: If access is denied.
        """
        file = self.get_file_by_id(file_id)
        privacy = file.privacy

        if privacy == Privacy.PUBLIC:
            return file

        if token is None:
            raise ForbiddenActionException("Authentication token is required for this resource.")

        processed_token = token.replace("Bearer ", "")

        try:
            user = get_user_from_jwt(processed_token, self._user_repository)
        except HTTPException as exc:
            raise ForbiddenActionException("Invalid token") from exc

        if (
            privacy == Privacy.PROTECTED
            and user.username not in file.shared_to
            and user.id != file.owner_id
        ):
            raise ForbiddenActionException("file is not shared with you")

        if privacy == Privacy.PRIVATE and user.id != file.owner_id:
            raise ForbiddenActionException("file is not shared with you")

        return file

    def create_file(
        self,
        user_path: UserPath,
        data: bytes,
        size: int,
        force: bool = False,
        privacy: Privacy = Privacy.PRIVATE,
    ) -> db_models.FileEntity:
        """Creates a new file with the given data.

        Args:
            user_path: The path where the file will be created.
            data: The binary content of the file.
            size: The size of the file in bytes.
            force: If True, overwrites an existing file.
            privacy: The privacy setting for the new file.

        Returns:
            The created file entity.

        Raises:
            ForbiddenActionException: If file name is empty or parent is special folder.
            ResourceAlreadyExistsException: If a resource with the same name exists (and not force).
        """
        if not user_path.name:
            raise ForbiddenActionException("Creation of file with no name is forbidden")

        file_name = user_path.name
        parent_path = user_path.parent
        parent = self._path_resolver.folder_from_path(parent_path)
        if parent.type != FolderType.NORMAL:
            raise ForbiddenActionException("You cannot create file in special folders")

        if force:
            try:
                self.delete_file(user_path)
            except ResourceNotFoundException:
                pass

        self._assert_no_children_matching_name(parent, file_name)

        new_file = self._file_repository.save(
            db_models.FileEntity(
                name=file_name, folder=parent, owner=user_path.owner, privacy=privacy, size=size
            )
        )

        self._save_file_data(file=new_file, data=data)

        return new_file

    def update_file(
        self, user_path: UserPath, privacy: Privacy, shared_to: list[str]
    ) -> db_models.FileEntity:
        """Updates the privacy and sharing list of a file.

        Args:
            user_path: The path to the file.
            privacy: The new privacy setting.
            shared_to: A list of usernames the file is shared with.

        Returns:
            The updated file entity.
        """
        file = self._path_resolver.file_from_path(user_path)
        file.privacy = privacy
        file.shared_to = shared_to
        return self._file_repository.save(file)

    def delete_file(self, user_path: UserPath):
        """Deletes a file and all links pointing to it.

        Args:
            user_path: The path to the file to delete.
        """
        file = self.get_file(user_path)
        links = self._link_repository.get_by_file_id(file.id)
        for link in links:
            link_path = self._path_resolver.path_from_link(link)
            self.delete_link(link_path)
        self._delete_file(file)

    def check_resource_type(self, user_path: UserPath) -> ResourceType:
        """Determines the type (file, folder, or link) of a resource at a path.

        Args:
            user_path: The path to check.

        Returns:
            The type of the resource.

        Raises:
            ResourceNotFoundException: If no resource is found at the path.
        """
        try:
            self.get_file(user_path)
            return ResourceType.FILE
        except ResourceNotFoundException:
            pass

        try:
            self.get_link(user_path)
            return ResourceType.LINK
        except ResourceNotFoundException:
            pass

        try:
            self.get_folder(user_path)
            return ResourceType.FOLDER
        except ResourceNotFoundException:
            pass

        raise ResourceNotFoundException(missing_resource_name=f"Resource {user_path} not found")

    def _delete_file(self, file: db_models.FileEntity):
        """Helper to delete file entity and its stored data."""
        self._file_repository.delete(file)
        self._delete_file_data(file)

    def get_file_data(self, user_path: UserPath) -> IO[bytes]:
        """Retrieves the binary data of a file by its path.

        Args:
            user_path: The path to the file.

        Returns:
            An I/O stream of the file's binary data.
        """
        file = self.get_file(user_path)
        return self._get_file_data(file)

    def get_shared_file_data(self, file_id: str) -> IO[bytes]:
        """Retrieves the binary data of a file by ID (for shared access).

        Args:
            file_id: The ID of the file.

        Returns:
            An I/O stream of the file's binary data.
        """
        file = self.get_file_by_id(file_id)
        return self._get_file_data(file)

    def potential_file_import(self, user_id: str, file_id: str):
        """Handles the logic for a user importing a file they have access to.

        If the file is not owned by the user but is shared with them (or public),
        this method adds it to their shared files list and creates a link
        in their "Shared/owner_username" folder.

        Args:
            user_id: The ID of the user importing the file.
            file_id: The ID of the file being imported.

        Raises:
            UserNotFoundException: If the importing user is not found.
        """
        file = self.get_file_by_id(file_id)
        if file.owner_id != user_id:
            if not self._shared_file_repository.is_file_shared_to_user(file_id, user_id):
                self.add_to_shared_files(user_id, file_id)
            user = self._user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundException()

            importing_user_folder_path = (
                UserPath.root_folder_of(user) / "Shared" / file.owner.username
            )
            try:
                self.get_folder(importing_user_folder_path)
            except ResourceNotFoundException:
                self.create_folder(
                    importing_user_folder_path, Privacy.PRIVATE, FolderType.SHARING_USER
                )

            link_path = importing_user_folder_path / file.name
            try:
                self.create_link_to_file(link_path, file)
            except ResourceAlreadyExistsException:
                pass

    def add_to_shared_files(self, user_id: str, file_id: str):
        """Adds a record indicating a file is shared with a user.

        Args:
            user_id: The ID of the user.
            file_id: The ID of the file.
        """
        self._shared_file_repository.save(
            db_models.SharedFileEntity(user_id=user_id, file_id=file_id)
        )

    def create_link_to_file(self, user_path: UserPath, file: db_models.FileEntity):
        """Creates a link at user_path pointing to the given file entity.

        Args:
            user_path: The path where the link will be created.
            file: The target file entity for the link.

        Returns:
            The created link entity.

        Raises:
            ResourceAlreadyExistsException: If a link to this file by this owner already exists.
        """
        if self._link_repository.get_by_file_id_and_owner_id(
            file_id=file.id, owner_id=user_path.owner.id
        ):
            logger.info(f"Link to file {file.name} already exists in {user_path}")
            raise ResourceAlreadyExistsException(
                f"Link to file {file.name} already exists in {user_path}"
            )
        link_name = user_path.name
        parent_path = user_path.parent
        parent = self._path_resolver.folder_from_path(parent_path)

        new_link = db_models.LinkEntity(
            name=link_name,
            folder=parent,
            owner=user_path.owner,
            resource_type=ResourceType.FILE.value,
            target_file=file,
        )
        return self._link_repository.save(new_link)

    def get_link(self, user_path: UserPath) -> db_models.LinkEntity:
        """Retrieves a link entity by its path.

        Args:
            user_path: The path to the link.

        Returns:
            The link entity.

        Raises:
            ResourceNotFoundException: If the link is not found.
        """
        folder = self.get_folder(user_path.parent)
        link = self._link_repository.get_by_name_and_parent(user_path.name, folder) # Renamed variable
        if link is None:
            raise ResourceNotFoundException(
                missing_resource_name=f"Link {user_path.name} not found"
            )
        return link

    def delete_link(self, user_path: UserPath):
        """Deletes a link. If it's the last link in a SHARING_USER folder, deletes folder too.

        Args:
            user_path: The path to the link to delete.
        """
        link = self.get_link(user_path)
        folder = self.get_folder(user_path.parent)
        if folder.type == FolderType.SHARING_USER:
            if link.target_file_id:
                self._shared_file_repository.delete_shared_files_from_users(
                    link.target_file_id, user_path.owner.id
                )
            self._link_repository.delete(link)
            if len(folder.links) == 0:
                self._folder_repository.delete(folder)
        else:
            self._link_repository.delete(link)

    def _save_file_data(self, file: db_models.FileEntity, data: bytes):
        """Saves file content to the storage service."""
        self._file_storage_service.save_file(data=data, file=file)

    def _get_file_data(self, file: db_models.FileEntity) -> IO[bytes]:
        """Retrieves file content from the storage service."""
        return self._file_storage_service.get_file(file=file)

    def _delete_file_data(self, file: db_models.FileEntity):
        """Deletes file content from the storage service."""
        return self._file_storage_service.delete_file(file)

    def create_root_folder(self, user_path: UserPath):
        """Creates a root folder for a user.

        Args:
            user_path: The path representing the root folder (name should be user ID).

        Raises:
            ValueError: If the path is not a proper root folder path.
            RootFolderAlreadyExistsException: If the root folder already exists.
        """
        if not user_path.is_root_folder():
            raise ValueError("Given path is not a proper root folder path")
        if self._get_root_folder_by_name(user_path.root_folder_name):
            raise RootFolderAlreadyExistsException("This root folder already exists")
        self._folder_repository.save(
            db_models.FolderEntity(name=user_path.root_folder_name, owner=user_path.owner)
        )

    def _get_root_folder_by_name(self, name: str) -> Optional[db_models.FolderEntity]:
        """Retrieves a root folder by name (typically user ID)."""
        return self._folder_repository.get_by_name_and_parent_id(name, None)

    def _assert_no_children_matching_name(self, folder: db_models.FolderEntity, name: str):
        """Asserts that no file or subfolder with the given name exists in the folder.

        Args:
            folder: The parent folder to check within.
            name: The name to check for conflicts.

        Raises:
            ResourceAlreadyExistsException: If a child with the same name exists.
        """
        exists_file_of_name = name in [file.name for file in folder.files]
        exists_folder_of_name = name in [subfolder.name for subfolder in folder.subfolders]
        if exists_file_of_name or exists_folder_of_name:
            raise ResourceAlreadyExistsException(
                 f"A resource named '{name}' already exists in this folder."
            )