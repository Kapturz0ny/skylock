import pytest
from unittest.mock import MagicMock, patch
from skylock.service.path_resolver import PathResolver
from skylock.service.resource_service import ResourceService
from skylock.utils.storage import FileStorageService
from skylock.database.repository import (
    FileRepository,
    FolderRepository,
    UserRepository,
    SharedFileRepository,
    LinkRepository,
)


@pytest.fixture
def mock_file_repository():
    return MagicMock(spec=FileRepository)


@pytest.fixture
def mock_folder_repository():
    return MagicMock(spec=FolderRepository)


@pytest.fixture
def mock_user_repository():
    return MagicMock(spec=UserRepository)


@pytest.fixture
def mock_shared_file_repository():
    return MagicMock(spec=SharedFileRepository)


@pytest.fixture
def mock_link_repository():
    return MagicMock(spec=LinkRepository)


@pytest.fixture
def mock_shared_file_repository():
    return MagicMock()


@pytest.fixture
def mock_link_repository():
    return MagicMock()


@pytest.fixture
def path_resolver(mock_file_repository, mock_folder_repository, mock_user_repository):
    return PathResolver(
        file_repository=mock_file_repository,
        folder_repository=mock_folder_repository,
        user_repository=mock_user_repository,
    )


@pytest.fixture
def storage_service(tmp_path):
    return FileStorageService(storage_path=tmp_path)


@pytest.fixture
def resource_service(
    mock_file_repository,
    mock_folder_repository,
    path_resolver,
    storage_service,
    mock_user_repository,
    mock_shared_file_repository,
    mock_link_repository,
):
    return ResourceService(
        file_repository=mock_file_repository,
        folder_repository=mock_folder_repository,
        path_resolver=path_resolver,
        file_storage_service=storage_service,
        user_repository=mock_user_repository,
        link_repository=mock_link_repository,
        shared_file_repository=mock_shared_file_repository,
    )
