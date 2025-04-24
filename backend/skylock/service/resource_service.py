from typing import IO, Optional, Literal

from skylock.database import models as db_models
from skylock.database.repository import (
    FileRepository,
    FolderRepository,
    UserRepository,
    SharedFileRepository,
)
from skylock.service.path_resolver import PathResolver
from skylock.utils.exceptions import (
    FolderNotEmptyException,
    ForbiddenActionException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    RootFolderAlreadyExistsException,
)
from skylock.utils.path import UserPath
from skylock.utils.storage import FileStorageService

from skylock.api.models import Privacy, FolderType
from skylock.utils.security import get_user_from_jwt

from fastapi import HTTPException
from skylock.utils.logger import logger


class ResourceService:
    def __init__(
        self,
        file_repository: FileRepository,
        folder_repository: FolderRepository,
        path_resolver: PathResolver,
        file_storage_service: FileStorageService,
        user_repository: UserRepository,
        shared_file_repository: SharedFileRepository,
    ):
        self._file_repository = file_repository
        self._folder_repository = folder_repository
        self._path_resolver = path_resolver
        self._file_storage_service = file_storage_service
        self._user_repository = user_repository
        self._shared_file_repository = shared_file_repository

    def get_folder(self, user_path: UserPath) -> db_models.FolderEntity:
        return self._path_resolver.folder_from_path(user_path)

    def get_folder_by_id(self, folder_id: str) -> db_models.FolderEntity:
        current_folder = self._folder_repository.get_by_id(folder_id)

        if current_folder is None:
            raise ResourceNotFoundException(missing_resource_name=folder_id)

        return current_folder

    def get_public_folder(self, folder_id: str) -> db_models.FolderEntity:
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
        folder = self._path_resolver.folder_from_path(user_path)
        self._update_folder(folder, privacy, recursive)
        return folder

    def _update_folder(
        self, folder: db_models.FolderEntity, privacy: Privacy, recursive: bool
    ) -> None:

        folder.privacy = privacy

        for file in folder.files:
            self._update_file(file, privacy)

        if recursive:
            for subfolder in folder.subfolders:
                self._update_folder(subfolder, privacy, recursive)

        self._folder_repository.save(folder)

    def _update_file(self, file: db_models.FileEntity, privacy: Privacy) -> None:
        file.privacy = privacy
        self._file_repository.save(file)

    def create_folder_with_parents(
        self, user_path: UserPath, privacy: Privacy = Privacy.PRIVATE
    ) -> db_models.FolderEntity:
        if user_path.is_root_folder():
            raise ForbiddenActionException("Creation of root folder is forbidden")

        for parent in reversed(user_path.parents):
            if not parent.is_root_folder() and not self._folder_exists(parent):
                self.create_folder(parent, privacy=privacy)

        return self.create_folder(user_path, privacy)

    def _folder_exists(self, user_path: UserPath) -> bool:
        try:
            self._path_resolver.folder_from_path(user_path)
            return True
        except ResourceNotFoundException:
            return False

    def delete_folder(self, user_path: UserPath, is_recursively: bool = False):
        folder = self._path_resolver.folder_from_path(user_path)
        self._delete_folder(folder, is_recursively=is_recursively)

    def _delete_folder(self, folder: db_models.FolderEntity, is_recursively: bool = False):
        if folder.is_root():
            raise ForbiddenActionException("Deletion of root folder is forbidden")

        if folder.type != FolderType.NORMAL:
            logger.warning(f"Attempted to delete a special folder: {folder.name}")
            raise ForbiddenActionException("You cannot delete special folders")

        has_folder_children = bool(folder.subfolders or folder.files)
        if not is_recursively and has_folder_children:
            raise FolderNotEmptyException

        for file in folder.files:
            self._delete_file(file)

        for subfolder in folder.subfolders:
            self._delete_folder(subfolder, is_recursively=True)

        self._folder_repository.delete(folder)

    def get_file(self, user_path: UserPath) -> db_models.FileEntity:
        return self._path_resolver.file_from_path(user_path)

    def get_file_by_id(self, file_id: str) -> db_models.FileEntity:
        file = self._file_repository.get_by_id(file_id)

        if file is None:
            raise ResourceNotFoundException(missing_resource_name=file_id)

        return file

    def get_verified_file(self, file_id: str, token) -> db_models.FileEntity:
        file = self.get_file_by_id(file_id)
        privacy = file.privacy
        token = token.replace("Bearer ", "")

        if privacy == Privacy.PUBLIC:
            return file

        try:
            user = get_user_from_jwt(token, self._user_repository)
        except HTTPException:
            raise ForbiddenActionException("Invalid token")

        if (
            privacy == Privacy.PROTECTED
            and user.username not in file.shared_to
            and user.id != file.owner_id
        ):
            raise ForbiddenActionException(f"file is not shared with you")

        if privacy == Privacy.PRIVATE and user.id != file.owner_id:
            raise ForbiddenActionException(f"file is not shared with you")

        return file

    def get_public_file(self, file_id: str) -> db_models.FileEntity:
        file = self.get_file_by_id(file_id)

        if file.privacy != Privacy.PUBLIC:
            raise ForbiddenActionException(f"folder with id {file_id} is not public")

        return file

    def create_file(
        self,
        user_path: UserPath,
        data: bytes,
        force: bool = False,
        privacy: Privacy = Privacy.PRIVATE,
    ) -> db_models.FileEntity:
        if not user_path.name:
            raise ForbiddenActionException("Creation of file with no name is forbidden")

        file_name = user_path.name
        parent_path = user_path.parent
        parent = self._path_resolver.folder_from_path(parent_path)

        if force:
            try:
                self.delete_file(user_path)
            except ResourceNotFoundException:
                pass

        self._assert_no_children_matching_name(parent, file_name)

        new_file = self._file_repository.save(
            db_models.FileEntity(
                name=file_name, folder=parent, owner=user_path.owner, privacy=privacy
            )
        )

        self._save_file_data(file=new_file, data=data)

        return new_file

    def update_file(
        self, user_path: UserPath, privacy: Privacy, shared_to: list[str]
    ) -> db_models.FileEntity:
        file = self._path_resolver.file_from_path(user_path)
        file.privacy = privacy
        file.shared_to = shared_to
        return self._file_repository.save(file)

    def delete_file(self, user_path: UserPath):
        file = self.get_file(user_path)
        self._delete_file(file)

    def _delete_file(self, file: db_models.FileEntity):
        self._file_repository.delete(file)
        self._delete_file_data(file)

    def get_file_data(self, user_path: UserPath) -> IO[bytes]:
        file = self.get_file(user_path)
        return self._get_file_data(file)

    def get_public_file_data(self, file_id: str) -> IO[bytes]:
        file = self.get_file_by_id(file_id)

        if file.privacy != Privacy.PUBLIC:
            raise ForbiddenActionException(f"File with id {file_id} is not public")

        return self._get_file_data(file)

    def get_shared_file_data(self, file_id: str) -> IO[bytes]:
        file = self.get_file_by_id(file_id)
        return self._get_file_data(file)

    def potential_file_import(self, user_id: str, file_id: str):
        file = self.get_file_by_id(file_id)
        if file.owner_id != user_id:
            if not self._shared_file_repository.is_file_shared_to_user(file_id, user_id):
                self.add_to_shared_files(user_id, file_id)

    def add_to_shared_files(self, user_id: str, file_id: str):
        self._shared_file_repository.save(
            db_models.SharedFileEntity(user_id=user_id, file_id=file_id)
        )

    def _save_file_data(self, file: db_models.FileEntity, data: bytes):
        self._file_storage_service.save_file(data=data, file=file)

    def _get_file_data(self, file: db_models.FileEntity) -> IO[bytes]:
        return self._file_storage_service.get_file(file=file)

    def _delete_file_data(self, file: db_models.FileEntity):
        return self._file_storage_service.delete_file(file)

    def create_root_folder(self, user_path: UserPath):
        if not user_path.is_root_folder():
            raise ValueError("Given path is not a proper root folder path")
        if self._get_root_folder_by_name(user_path.root_folder_name):
            raise RootFolderAlreadyExistsException("This root folder already exists")
        self._folder_repository.save(
            db_models.FolderEntity(name=user_path.root_folder_name, owner=user_path.owner)
        )

    def _get_root_folder_by_name(self, name: str) -> Optional[db_models.FolderEntity]:
        return self._folder_repository.get_by_name_and_parent_id(name, None)

    def _assert_no_children_matching_name(self, folder: db_models.FolderEntity, name: str):
        exists_file_of_name = name in [file.name for file in folder.files]
        exists_folder_of_name = name in [folder.name for folder in folder.subfolders]
        if exists_file_of_name or exists_folder_of_name:
            raise ResourceAlreadyExistsException
