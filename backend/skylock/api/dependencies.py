from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from skylock.database.models import UserEntity
from skylock.database.repository import FileRepository, FolderRepository, UserRepository
from skylock.database.session import get_db_session
from skylock.service.path_resolver import PathResolver
from skylock.service.resource_service import ResourceService
from skylock.service.response_builder import ResponseBuilder
from skylock.service.user_service import UserService
from skylock.service.zip_service import ZipService
from skylock.skylock_facade import SkylockFacade
from skylock.utils.security import get_user_from_jwt, oauth2_scheme
from skylock.utils.storage import FileStorageService
from skylock.utils.url_generator import UrlGenerator


def get_user_repository(db: Annotated[Session, Depends(get_db_session)]) -> UserRepository:
    return UserRepository(db)


def get_folder_repository(db: Annotated[Session, Depends(get_db_session)]) -> FolderRepository:
    return FolderRepository(db)


def get_file_repository(db: Annotated[Session, Depends(get_db_session)]) -> FileRepository:
    return FileRepository(db)


def get_user_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)]
) -> UserService:
    return UserService(user_repository)


def get_path_resolver(
    file_repository: Annotated[FileRepository, Depends(get_file_repository)],
    folder_repository: Annotated[FolderRepository, Depends(get_folder_repository)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> PathResolver:
    return PathResolver(
        file_repository=file_repository,
        folder_repository=folder_repository,
        user_repository=user_repository,
    )


def get_storage_service():
    return FileStorageService()


def get_resource_service(
    file_repository: Annotated[FileRepository, Depends(get_file_repository)],
    folder_repository: Annotated[FolderRepository, Depends(get_folder_repository)],
    path_resolver: Annotated[PathResolver, Depends(get_path_resolver)],
    storage_service: Annotated[FileStorageService, Depends(get_storage_service)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> ResourceService:
    return ResourceService(
        file_repository=file_repository,
        folder_repository=folder_repository,
        path_resolver=path_resolver,
        file_storage_service=storage_service,
        user_repository=user_repository
    )


def get_response_builder() -> ResponseBuilder:
    return ResponseBuilder()


def get_url_generator() -> UrlGenerator:
    return UrlGenerator()


def get_zip_service(
    storage_service: Annotated[FileStorageService, Depends(get_storage_service)],
) -> ZipService:
    return ZipService(storage_service)


def get_skylock_facade(
    user_service: Annotated[UserService, Depends(get_user_service)],
    resource_service: Annotated[ResourceService, Depends(get_resource_service)],
    path_resolver: Annotated[PathResolver, Depends(get_path_resolver)],
    response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
    url_generator: Annotated[UrlGenerator, Depends(get_url_generator)],
    zip_service: Annotated[ZipService, Depends(get_zip_service)],
) -> SkylockFacade:
    return SkylockFacade(
        user_service=user_service,
        resource_service=resource_service,
        url_generator=url_generator,
        path_resolver=path_resolver,
        response_builder=response_builder,
        zip_service=zip_service,
    )


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserEntity:
    return get_user_from_jwt(token=token, user_repository=user_repository)
