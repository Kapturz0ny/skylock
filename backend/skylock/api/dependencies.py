from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from skylock.database.models import UserEntity
from skylock.database.repository import (
    FileRepository,
    FolderRepository,
    UserRepository,
    SharedFileRepository,
    LinkRepository,
)
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
    """Creates and returns a user repository.

    Args:
        db (Session): Database session.

    Returns:
        UserRepository: User repository instance.
    """
    return UserRepository(db)


def get_folder_repository(db: Annotated[Session, Depends(get_db_session)]) -> FolderRepository:
    """Creates and returns a folder repository.

    Args:
        db (Session): Database session.

    Returns:
        FolderRepository: Folder repository instance.
    """
    return FolderRepository(db)


def get_file_repository(db: Annotated[Session, Depends(get_db_session)]) -> FileRepository:
    """Creates and returns a file repository.

    Args:
        db (Session): Database session.

    Returns:
        FileRepository: File repository instance.
    """
    return FileRepository(db)


def get_shared_file_repository(
    db: Annotated[Session, Depends(get_db_session)]
) -> SharedFileRepository:
    """Creates and returns a shared file repository.

    Args:
        db (Session): Database session.

    Returns:
        SharedFileRepository: Shared file repository instance.
    """
    return SharedFileRepository(db)


def get_link_repository(db: Annotated[Session, Depends(get_db_session)]) -> LinkRepository:
    """Creates and returns a link repository.

    Args:
        db (Session): Database session.

    Returns:
        LinkRepository: Link repository instance.
    """
    return LinkRepository(db)


def get_user_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)]
) -> UserService:
    """Creates and returns a user service.

    Args:
        user_repository (UserRepository): User repository.

    Returns:
        UserService: User service instance.
    """
    return UserService(user_repository)


def get_path_resolver(
    file_repository: Annotated[FileRepository, Depends(get_file_repository)],
    folder_repository: Annotated[FolderRepository, Depends(get_folder_repository)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> PathResolver:
    """Creates and returns a path resolver.

    Args:
        file_repository (FileRepository): File repository.
        folder_repository (FolderRepository): Folder repository.
        user_repository (UserRepository): User repository.

    Returns:
        PathResolver: Path resolver instance.
    """
    return PathResolver(
        file_repository=file_repository,
        folder_repository=folder_repository,
        user_repository=user_repository,
    )


def get_storage_service() -> FileStorageService:
    """Creates and returns a file storage service.

    Returns:
        FileStorageService: File storage service instance.
    """
    return FileStorageService()


def get_resource_service(
    file_repository: Annotated[FileRepository, Depends(get_file_repository)],
    folder_repository: Annotated[FolderRepository, Depends(get_folder_repository)],
    path_resolver: Annotated[PathResolver, Depends(get_path_resolver)],
    storage_service: Annotated[FileStorageService, Depends(get_storage_service)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    shared_file_repository: Annotated[SharedFileRepository, Depends(get_shared_file_repository)],
    link_repository: Annotated[LinkRepository, Depends(get_link_repository)],
) -> ResourceService:
    """Creates and returns a resource service.

    Args:
        file_repository (FileRepository): File repository.
        folder_repository (FolderRepository): Folder repository.
        path_resolver (PathResolver): Path resolver.
        storage_service (FileStorageService): File storage service.
        user_repository (UserRepository): User repository.
        shared_file_repository (SharedFileRepository): Shared file repository.
        link_repository (LinkRepository): Link repository.

    Returns:
        ResourceService: Resource service instance.
    """
    return ResourceService(
        file_repository=file_repository,
        folder_repository=folder_repository,
        path_resolver=path_resolver,
        file_storage_service=storage_service,
        user_repository=user_repository,
        shared_file_repository=shared_file_repository,
        link_repository=link_repository,
    )


def get_response_builder() -> ResponseBuilder:
    """Creates and returns a response builder.

    Returns:
        ResponseBuilder: Response builder instance.
    """
    return ResponseBuilder()


def get_url_generator() -> UrlGenerator:
    """Creates and returns a URL generator.

    Returns:
        UrlGenerator: URL generator instance.
    """
    return UrlGenerator()


def get_zip_service(
    storage_service: Annotated[FileStorageService, Depends(get_storage_service)],
) -> ZipService:
    """Creates and returns a ZIP service.

    Args:
        storage_service (FileStorageService): File storage service.

    Returns:
        ZipService: ZIP service instance.
    """
    return ZipService(storage_service)


def get_skylock_facade(
    user_service: Annotated[UserService, Depends(get_user_service)],
    resource_service: Annotated[ResourceService, Depends(get_resource_service)],
    path_resolver: Annotated[PathResolver, Depends(get_path_resolver)],
    response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
    url_generator: Annotated[UrlGenerator, Depends(get_url_generator)],
    zip_service: Annotated[ZipService, Depends(get_zip_service)],
) -> SkylockFacade:
    """Creates and returns the main Skylock application facade.

    Args:
        user_service (UserService): User service.
        resource_service (ResourceService): Resource service.
        path_resolver (PathResolver): Path resolver.
        response_builder (ResponseBuilder): Response builder.
        url_generator (UrlGenerator): URL generator.
        zip_service (ZipService): ZIP service.

    Returns:
        SkylockFacade: Skylock facade instance.
    """
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
    """Retrieves the current user based on the JWT token.

    Args:
        token (str): JWT token.
        user_repository (UserRepository): User repository.

    Returns:
        UserEntity: Logged-in user entity.
    """
    return get_user_from_jwt(token=token, user_repository=user_repository)
