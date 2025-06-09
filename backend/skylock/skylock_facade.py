from skylock.service.path_resolver import PathResolver
from skylock.service.resource_service import ResourceService
from skylock.service.response_builder import ResponseBuilder
from skylock.service.user_service import UserService
from skylock.service.zip_service import ZipService
from skylock.service.dramatiq_tasks import create_zip_task
from skylock.api import models
from skylock.api.models import Privacy, FolderType
from skylock.utils.exceptions import ForbiddenActionException, ResourceNotFoundException
from skylock.utils.path import UserPath
from skylock.utils.url_generator import UrlGenerator
from skylock.database import models as db_models


class SkylockFacade:
    """
    Provides a unified interface to Skylock's core functionalities,
    orchestrating various services for user and resource management.
    """

    def __init__(
        self,
        *,
        user_service: UserService,
        resource_service: ResourceService,
        path_resolver: PathResolver,
        url_generator: UrlGenerator,
        response_builder: ResponseBuilder,
        zip_service: ZipService,
    ):
        """Initializes the SkylockFacade with its dependent services.

        Args:
            user_service: Service for user authentication and management.
            resource_service: Service for managing files and folders.
            path_resolver: Service for resolving paths of resources.
            url_generator: Service for generating shareable URLs.
            response_builder: Service for constructing API response models.
            zip_service: Service for creating ZIP archives.
        """
        self._user_service = user_service
        self._resource_service = resource_service
        self._path_resolver = path_resolver
        self._url_generator = url_generator
        self._response_builder = response_builder
        self._zip_service = zip_service

    # User Management Methods
    def register_user(self, username: str, email: str) -> None:
        """Initiates the registration process for a new user.

        Delegates to UserService to handle 2FA code sending.

        Args:
            username: The desired username.
            email: The user's email address.
        """
        self._user_service.register_user(username, email)

    def verify_2fa(
        self, username: str, password: str, code: str, email: str
    ) -> db_models.UserEntity:
        """Verifies a 2FA code and completes user registration.

        Delegates to UserService.

        Args:
            username: The username.
            password: The chosen password.
            code: The 2FA code from the user.
            email: The user's email address.

        Returns:
            The created `db_models.UserEntity` upon successful verification.
        """
        return self._user_service.verify_2fa(username, password, code, email)

    def login_user(self, username: str, password: str) -> models.Token:
        """Logs in an existing user.

        Delegates to UserService to authenticate and generate a token.

        Args:
            username: The username.
            password: The password.

        Returns:
            A `models.Token` object containing the access token.
        """
        return self._user_service.login_user(username, password)

    # Folder Operations
    def create_folder(
        self,
        user_path: UserPath,
        with_parents: bool = False,
        privacy: Privacy = Privacy.PRIVATE,
        folder_type: FolderType = FolderType.NORMAL,
    ) -> models.Folder:
        """Creates a new folder at the specified user path.

        Args:
            user_path: The path where the folder should be created, including owner and location.
            with_parents: If True, creates any missing parent directories.
            privacy: The privacy setting for the new folder.
            folder_type: The type of folder (e.g., NORMAL, SHARED).

        Returns:
            A `models.Folder` response model representing the created folder.
        """
        if with_parents:
            folder = self._resource_service.create_folder_with_parents(
                user_path=user_path, privacy=privacy
            )
        else:
            folder = self._resource_service.create_folder(
                user_path=user_path, privacy=privacy, folder_type=folder_type
            )

        return self._response_builder.get_folder_response(folder=folder, user_path=user_path)

    def download_folder(self, user_path: UserPath) -> models.FolderData:
        """Downloads a folder as a ZIP archive.

        Retrieves the folder, zips its contents, and prepares a download response.

        Args:
            user_path: The path of the folder to download.

        Returns:
            A `models.FolderData` response model containing the folder name and ZIP data stream.
        """
        folder = self._resource_service.get_folder(user_path)
        data, _ = self._zip_service.create_zip_from_folder(folder)  # size is ignored here
        return self._response_builder.get_folder_data_response(folder=folder, folder_data=data)

    def get_folder_contents(self, user_path: UserPath) -> models.FolderContents:
        """Retrieves the contents (files, subfolders, links) of a specified folder.

        Args:
            user_path: The path of the folder whose contents are to be listed.

        Returns:
            A `models.FolderContents` response model detailing the folder's children.
        """
        folder = self._resource_service.get_folder(user_path)
        return self._response_builder.get_folder_contents_response(
            folder=folder, user_path=user_path
        )

    def get_public_folder_contents(self, folder_id: str) -> models.FolderContents:
        """Retrieves the contents of a publicly accessible folder by its ID.

        Args:
            folder_id: The unique ID of the public folder.

        Returns:
            A `models.FolderContents` response model.
        """
        folder = self._resource_service.get_public_folder(folder_id)
        path = self._path_resolver.path_from_folder(folder)
        return self._response_builder.get_folder_contents_response(folder=folder, user_path=path)

    def update_folder(
        self, user_path: UserPath, privacy: Privacy, recursive: bool
    ) -> models.Folder:
        """Updates the properties of a folder, such as its privacy.

        Args:
            user_path: The path of the folder to update.
            privacy: The new privacy setting for the folder.
            recursive: If True, applies the privacy change to all sub-items.

        Returns:
            A `models.Folder` response model representing the updated folder.
        """
        folder = self._resource_service.update_folder(user_path, privacy, recursive)
        return self._response_builder.get_folder_response(folder=folder, user_path=user_path)

    def delete_folder(self, user_path: UserPath, is_recursively: bool = False) -> None:
        """Deletes a folder.

        Args:
            user_path: The path of the folder to delete.
            is_recursively: If True, deletes the folder and all its contents.
                            If False and folder is not empty, an error might occur (service-dependent).
        """
        self._resource_service.delete_folder(user_path, is_recursively=is_recursively)

    def get_folder_url(self, user_path: UserPath) -> str:
        """Generates a shareable URL for a public folder.

        Args:
            user_path: The path of the folder.

        Returns:
            A string containing the shareable URL.

        Raises:
            ForbiddenActionException: If the folder is not public.
        """
        folder = self._resource_service.get_folder(user_path)

        if not folder.privacy == Privacy.PUBLIC:
            raise ForbiddenActionException(f"Folder {folder.name} is not public, cannot be shared")

        return self._url_generator.generate_url_for_folder(folder.id)

    def create_zip(self, user_path: UserPath, force: bool) -> dict:
        """Initiates an asynchronous task to create a ZIP archive for a folder.

        Acquires a lock to prevent concurrent zipping and dispatches a background task.

        Args:
            user_path: The path of the folder to be zipped.
            force: If True, overwrites an existing ZIP if one is being generated or exists.
                   (Behavior of force might depend on ZipService and task implementation).

        Returns:
            A dictionary message indicating that zip generation has started.

        Raises:
            ZipQueueError: If a zipping task for this folder is already in progress (from `_zip_service.acquire_zip_lock`).
        """
        self._resource_service.zip_exists(user_path, force)

        self._resource_service.get_folder(user_path)
        task_key = self._zip_service.acquire_zip_lock(user_path.owner.id, user_path.path)
        create_zip_task.send(
            user_path.owner.id,
            user_path.path,
            force,
            task_name=task_key,
        )
        return {"message": "Zip generation started."}

    # File Operations
    def upload_file(
        self,
        user_path: UserPath,
        file_data: bytes,
        size: int,
        force: bool = False,
        privacy: Privacy = Privacy.PRIVATE,
    ) -> models.File:
        """Uploads a new file to the specified user path.

        Args:
            user_path: The full path (including filename) where the file should be stored.
            file_data: The binary content of the file.
            size: The size of the file in bytes.
            force: If True, overwrites an existing file at the same path.
            privacy: The privacy setting for the new file.

        Returns:
            A `models.File` response model representing the uploaded file.
        """
        file = self._resource_service.create_file(user_path, file_data, size, force, privacy)
        return self._response_builder.get_file_response(file=file, user_path=user_path)

    def download_file(self, user_path: UserPath) -> models.FileData:
        """Downloads a file's content.

        Args:
            user_path: The path of the file to download.

        Returns:
            A `models.FileData` response model containing file metadata and data stream.
        """
        file = self._resource_service.get_file(user_path=user_path)
        data = self._resource_service.get_file_data(user_path)
        return self._response_builder.get_file_data_response(file=file, file_data=data)

    def download_shared_file_by_id(self, file_id: str, token=None) -> models.FileData:
        """Downloads a file that might be shared, potentially requiring a token for access.

        Args:
            file_id: The unique ID of the file.
            token: An optional access token if the file requires specific authorization.

        Returns:
            A `models.FileData` response model.
        """
        file = self._resource_service.get_verified_file(file_id, token)
        data = self._resource_service.get_shared_file_data(file_id)
        return self._response_builder.get_file_data_response(file=file, file_data=data)

    def download_shared_file_by_path(self, path: str, token=None) -> models.FileData:
        """Downloads a file that might be shared, potentially requiring a token for access.

        Args:
            file_id: The unique ID of the file.
            token: An optional access token if the file requires specific authorization.

        Returns:
            A `models.FileData` response model.
        """
        file = self._resource_service.get_file_by_token_path(path, token)
        return self.download_shared_file_by_id(file.id, token)

    def update_file(
        self, user_path: UserPath, privacy: Privacy, shared_to: list[str]
    ) -> models.File:
        """Updates the properties of a file, such as privacy and sharing list.

        Manages shared file links and permissions based on privacy changes.

        Args:
            user_path: The path of the file to update.
            privacy: The new privacy setting.
            shared_to: A list of usernames with whom the file should be shared (relevant for PROTECTED privacy).

        Returns:
            A `models.File` response model representing the updated file.
        """
        current_file = self._resource_service.get_file(user_path)

        # PUBLIC, PROTECTED -> PRIVATE
        # delete shared_files connected to this file from all users
        if privacy == Privacy.PRIVATE:
            current_shared_files = (
                self._resource_service._shared_file_repository.get_shared_files_by_file_id(
                    current_file.id
                )
            )
            for shared_file in current_shared_files:
                linked_file = self._resource_service._link_repository.get_by_file_id_and_owner_id(
                    current_file.id, shared_file.user_id
                )
                if linked_file:
                    folder_path = self._path_resolver.path_from_folder(linked_file.folder)
                    self.delete_file(folder_path / linked_file.name)
                self._resource_service._shared_file_repository.delete_shared_files_from_users(
                    current_file.id, shared_file.user_id
                )
            found = []

        # PUBLIC -> PROTECTED
        # delete shared_files from users that are not on shared_to list
        elif privacy == Privacy.PROTECTED and current_file.privacy == Privacy.PUBLIC:
            for sharing in current_file.shared_with:
                if sharing.user.username not in set(current_file.shared_to).union(shared_to):
                    linked_file = (
                        self._resource_service._link_repository.get_by_file_id_and_owner_id(
                            current_file.id, sharing.user_id
                        )
                    )
                    if linked_file:
                        folder_path = self._path_resolver.path_from_folder(linked_file.folder)
                        self.delete_file(folder_path / linked_file.name)
                    self._resource_service._shared_file_repository.delete_shared_files_from_users(
                        current_file.id, sharing.user_id
                    )
            found = list(
                set(current_file.shared_to).union(
                    self._user_service.find_shared_to_users(shared_to)
                )
            )

        # don't change anything in shared_files table
        else:
            found = list(
                set(current_file.shared_to).union(
                    self._user_service.find_shared_to_users(shared_to)
                )
            )
        file = self._resource_service.update_file(user_path, privacy, found)
        return self._response_builder.get_file_response(file=file, user_path=user_path)

    def delete_file(self, user_path: UserPath) -> None:
        """Deletes a file or a link at the specified path.

        Args:
            user_path: The path of the file or link to delete.

        Raises:
            ForbiddenActionException: If the resource at the path is not a file or link.
        """
        resource_type = self._resource_service.check_resource_type(user_path)
        if resource_type == models.ResourceType.FILE:
            self._resource_service.delete_file(user_path)
        elif resource_type == models.ResourceType.LINK:
            self._resource_service.delete_link(user_path)
        else:
            raise ForbiddenActionException(
                f"Resource at {user_path.path} is not a deletable file or link type."
            )

    def get_file_url(self, user_path: UserPath) -> str:
        """Generates a shareable URL for a file.

        Note: Current implementation does not check file privacy before generating URL.

        Args:
            user_path: The path of the file.

        Returns:
            A string containing the shareable URL.
        """
        file = self._resource_service.get_file(user_path)
        return self._url_generator.generate_url_for_file(file.id)

    # Public Resource Access
    def get_file_for_login(self, file_id: str) -> models.File:
        """Retrieves file metadata for a file identified by its ID.

        Typically used when a user is accessing a file directly via ID,
        e.g., through a shared link before full authentication for other operations.

        Args:
            file_id: The unique ID of the file.

        Returns:
            A `models.File` response model.
        """
        file = self._resource_service.get_file_by_id(file_id)
        path = self._path_resolver.path_from_file(file)
        return self._response_builder.get_file_response(file=file, user_path=path)

    def configure_new_user(self, user: db_models.UserEntity) -> None:
        """Sets up initial resources for a newly registered user.

        Creates a root folder and a default 'Shared' folder.

        Args:
            user: The `db_models.UserEntity` of the new user.
        """
        self._resource_service.create_root_folder(UserPath.root_folder_of(user))
        self._resource_service.create_folder(
            user_path=UserPath.root_folder_of(user) / "Shared",
            privacy=Privacy.PRIVATE,
            folder_type=FolderType.SHARED,
        )
