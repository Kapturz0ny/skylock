from skylock.service.path_resolver import PathResolver
from skylock.service.resource_service import ResourceService
from skylock.service.response_builder import ResponseBuilder
from skylock.service.user_service import UserService
from skylock.service.zip_service import ZipService
from skylock.api import models
from skylock.api.models import Privacy
from skylock.utils.exceptions import ForbiddenActionException
from skylock.utils.path import UserPath
from skylock.utils.url_generator import UrlGenerator
from typing import Literal



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
    def register_user(self, username: str, password: str, email: str):
        user = self._user_service.register_user(username, password, email)
        # self._resource_service.create_root_folder(UserPath.root_folder_of(user))

    def verify_2FA(self, username: str, password: str, code: str, email: str):
        user = self._user_service.verify_2FA(username, password, code, email)
        self._resource_service.create_root_folder(UserPath.root_folder_of(user))

    def login_user(self, username: str, password: str) -> models.Token:
        return self._user_service.login_user(username, password)

    # Folder Operations
    def create_folder(
        self, user_path: UserPath, with_parents: bool = False, public: bool = False
    ) -> models.Folder:
        if with_parents:
            folder = self._resource_service.create_folder_with_parents(
                user_path=user_path, public=public
            )
        else:
            folder = self._resource_service.create_folder(user_path=user_path, public=public)

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

    def update_folder(self, user_path: UserPath, is_public: bool, recursive: bool) -> models.Folder:
        folder = self._resource_service.update_folder(user_path, is_public, recursive)
        return self._response_builder.get_folder_response(folder=folder, user_path=user_path)

    def delete_folder(self, user_path: UserPath, is_recursively: bool = False):
        self._resource_service.delete_folder(user_path, is_recursively=is_recursively)

    def get_folder_url(self, user_path: UserPath) -> str:
        folder = self._resource_service.get_folder(user_path)

        if not folder.is_public:
            raise ForbiddenActionException(f"Folder {folder.name} is not public, cannot be shared")

        return self._url_generator.generate_url_for_folder(folder.id)

    # File Operations
    def upload_file(
        self, user_path: UserPath, file_data: bytes, force: bool = False, privacy: Privacy = Privacy.PRIVATE
    ) -> models.File:
        file = self._resource_service.create_file(user_path, file_data, force, privacy)
        return self._response_builder.get_file_response(file=file, user_path=user_path)

    def download_file(self, user_path: UserPath) -> models.FileData:
        file = self._resource_service.get_file(user_path=user_path)
        data = self._resource_service.get_file_data(user_path)
        return self._response_builder.get_file_data_response(file=file, file_data=data)

    def download_public_file(self, file_id: str) -> models.FileData:
        file = self._resource_service.get_public_file(file_id)
        data = self._resource_service.get_public_file_data(file_id)
        return self._response_builder.get_file_data_response(file=file, file_data=data)

    def update_file(self, user_path: UserPath, privacy: Privacy, shared_to: list[str]) -> models.File:
        found = self._user_service.find_shared_to_users(shared_to)
        file = self._resource_service.update_file(user_path, privacy, found)
        return self._response_builder.get_file_response(file=file, user_path=user_path)

    def delete_file(self, user_path: UserPath):
        self._resource_service.delete_file(user_path)

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