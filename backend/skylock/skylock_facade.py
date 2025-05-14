from skylock.service.path_resolver import PathResolver
from skylock.service.resource_service import ResourceService
from skylock.service.response_builder import ResponseBuilder
from skylock.service.user_service import UserService
from skylock.service.zip_service import ZipService
from skylock.api import models
from skylock.api.models import Privacy, FolderType
from skylock.utils.exceptions import ForbiddenActionException
from skylock.utils.path import UserPath
from skylock.utils.url_generator import UrlGenerator
from skylock.database import models as db_models


class SkylockFacade:
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
        self._user_service = user_service
        self._resource_service = resource_service
        self._path_resolver = path_resolver
        self._url_generator = url_generator
        self._response_builder = response_builder
        self._zip_service = zip_service

    # User Management Methods
    def register_user(self, username: str, password: str, email: str) -> None:
        user = self._user_service.register_user(username, password, email)
        # self._resource_service.create_root_folder(UserPath.root_folder_of(user))

    def verify_2FA(
        self, username: str, password: str, code: str, email: str
    ) -> db_models.UserEntity:
        return self._user_service.verify_2FA(username, password, code, email)

    def login_user(self, username: str, password: str) -> models.Token:
        return self._user_service.login_user(username, password)

    # Folder Operations
    def create_folder(
        self,
        user_path: UserPath,
        with_parents: bool = False,
        privacy: Privacy = Privacy.PRIVATE,
        folder_type: FolderType = FolderType.NORMAL,
    ) -> models.Folder:
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
        folder = self._resource_service.get_folder(user_path)
        data = self._zip_service.create_zip_from_folder(folder)
        return self._response_builder.get_folder_data_response(folder=folder, folder_data=data)

    def get_folder_contents(self, user_path: UserPath) -> models.FolderContents:
        folder = self._resource_service.get_folder(user_path)
        return self._response_builder.get_folder_contents_response(
            folder=folder, user_path=user_path
        )

    def get_public_folder_contents(self, folder_id: str) -> models.FolderContents:
        folder = self._resource_service.get_public_folder(folder_id)
        path = self._path_resolver.path_from_folder(folder)
        return self._response_builder.get_folder_contents_response(folder=folder, user_path=path)

    def update_folder(
        self, user_path: UserPath, privacy: Privacy, recursive: bool
    ) -> models.Folder:
        folder = self._resource_service.update_folder(user_path, privacy, recursive)
        return self._response_builder.get_folder_response(folder=folder, user_path=user_path)

    def delete_folder(self, user_path: UserPath, is_recursively: bool = False):
        self._resource_service.delete_folder(user_path, is_recursively=is_recursively)

    def get_folder_url(self, user_path: UserPath) -> str:
        folder = self._resource_service.get_folder(user_path)

        if not folder.privacy == Privacy.PUBLIC:
            raise ForbiddenActionException(f"Folder {folder.name} is not public, cannot be shared")

        return self._url_generator.generate_url_for_folder(folder.id)

    # File Operations
    def upload_file(
        self,
        user_path: UserPath,
        file_data: bytes,
        size: int,
        force: bool = False,
        privacy: Privacy = Privacy.PRIVATE,
    ) -> models.File:
        file = self._resource_service.create_file(user_path, file_data, size, force, privacy)
        return self._response_builder.get_file_response(file=file, user_path=user_path)

    def download_file(self, user_path: UserPath) -> models.FileData:
        file = self._resource_service.get_file(user_path=user_path)
        data = self._resource_service.get_file_data(user_path)
        return self._response_builder.get_file_data_response(file=file, file_data=data)

    def download_public_file(self, file_id: str) -> models.FileData:
        file = self._resource_service.get_public_file(file_id)
        data = self._resource_service.get_public_file_data(file_id)
        return self._response_builder.get_file_data_response(file=file, file_data=data)

    def download_shared_file(self, file_id: str, token=None) -> models.FileData:
        file = self._resource_service.get_verified_file(file_id, token)
        data = self._resource_service.get_shared_file_data(file_id)
        return self._response_builder.get_file_data_response(file=file, file_data=data)

    def update_file(
        self, user_path: UserPath, privacy: Privacy, shared_to: list[str]
    ) -> models.File:
        # current file state (before modification)
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
                if sharing.user.username not in current_file.shared_to.union(shared_to):
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
            found = current_file.shared_to.union(self._user_service.find_shared_to_users(shared_to))

        # don't change anything in shared_files table
        else:
            found = current_file.shared_to.union(self._user_service.find_shared_to_users(shared_to))
        file = self._resource_service.update_file(user_path, privacy, found)
        return self._response_builder.get_file_response(file=file, user_path=user_path)

    def delete_file(self, user_path: UserPath):
        resource_type = self._resource_service.check_resource_type(user_path)
        if resource_type == models.ResourceType.FILE:
            self._resource_service.delete_file(user_path)
        elif resource_type == models.ResourceType.LINK:
            self._resource_service.delete_link(user_path)
        else:
            raise ForbiddenActionException(f"Resource {user_path} is not a file or link")

    def get_file_url(self, user_path: UserPath) -> str:
        file = self._resource_service.get_file(user_path)
        return self._url_generator.generate_url_for_file(file.id)

        # raise ForbiddenActionException(f"File {file.name} is not available for this user, cannot be shared")

    # Public Resource Access
    def get_public_file(self, file_id: str) -> models.File:
        file = self._resource_service.get_public_file(file_id)
        path = self._path_resolver.path_from_file(file)
        return self._response_builder.get_file_response(file=file, user_path=path)

    def get_file_for_login(self, file_id: str) -> models.File:
        file = self._resource_service.get_file_by_id(file_id)
        path = self._path_resolver.path_from_file(file)
        return self._response_builder.get_file_response(file=file, user_path=path)

    def configure_new_user(self, user: db_models.UserEntity) -> None:
        self._resource_service.create_root_folder(UserPath.root_folder_of(user))
        self._resource_service.create_folder(
            user_path=UserPath.root_folder_of(user) / "Shared",
            privacy=Privacy.PRIVATE,
            folder_type=FolderType.SHARED,
        )
