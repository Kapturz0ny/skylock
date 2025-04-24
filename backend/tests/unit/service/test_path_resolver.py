from starlette.responses import FileResponse
from skylock.database.models import FileEntity, FolderEntity, UserEntity
from skylock.database.repository import FolderRepository, UserRepository, FileRepository
from skylock.utils.exceptions import ResourceNotFoundException
from skylock.utils.path import UserPath
import pytest
from skylock.service.path_resolver import PathResolver


from sqlalchemy import StaticPool, create_engine
from skylock.database.models import Base
from sqlalchemy.orm import sessionmaker


TEST_DATABASE_URL = "sqlite://"

MOCK_USERNAME = "mockuser"
MOCK_PASSWORD = "mockpasswd"


@pytest.fixture
def db_session():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = factory()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_user_repository(db_session):
    ur = UserRepository(db_session)
    new_user_entity = UserEntity(id="user-123", username="testuser", password="testuser123")
    ur.save(new_user_entity)
    return ur


@pytest.fixture
def mock_folder_repository(db_session, mock_user_repository):
    """fixture representing hirarchy of folders as:
    root_folder/
        |- test_folder/
                |- test_subfolder/
    """
    fr = FolderRepository(db_session)
    user = mock_user_repository.get_by_username("testuser")
    assert user is not None
    user_path = UserPath.root_folder_of(user)

    root_folder = FolderEntity(id="folder-123", name=user_path.root_folder_name, owner=user)
    fr.save(root_folder)

    folder = FolderEntity(
        id="folder-456", name="test_folder", owner=user, parent_folder=root_folder
    )
    fr.save(folder)

    subfolder = FolderEntity(
        id="folder-789", name="test_subfolder", owner=user, parent_folder=folder
    )
    fr.save(subfolder)

    return fr


@pytest.fixture
def mock_file_repository(db_session, mock_folder_repository):
    """fixture representing hirarchy of files as:
    root_folder/
        |- test_file
        |- test_folder/
                |- test_subfolder/
                |- test_subfile/
    """
    fr = FileRepository(db_session)

    root_level_file = FileEntity(
        id="file-123", name="test_file", folder_id="folder-123", owner_id="user-123"
    )
    fr.save(root_level_file)

    test_subfile = FileEntity(
        id="file-456", name="test_subfile", folder_id="folder-456", owner_id="user-123"
    )
    fr.save(test_subfile)

    return fr


@pytest.fixture
def path_resolver(mock_file_repository, mock_folder_repository, mock_user_repository):
    return PathResolver(
        file_repository=mock_file_repository,
        folder_repository=mock_folder_repository,
        user_repository=mock_user_repository,
    )


def test_folder_from_path_root_success(path_resolver):
    user = path_resolver._user_repository.get_by_username("testuser")
    user_path = UserPath.root_folder_of(user)

    result = path_resolver.folder_from_path(user_path)
    assert result.id == "folder-123"
    assert result.name == user.id
    assert len(result.subfolders) == 1


def test_folder_from_path_subfolder_success(path_resolver):
    user = path_resolver._user_repository.get_by_username("testuser")
    user_path = UserPath(path="test_folder", owner=user)

    result = path_resolver.folder_from_path(user_path)
    assert result.id == "folder-456"
    assert result.name == "test_folder"
    assert len(result.subfolders) == 1


def test_folder_from_path_deep_subfolder_success(path_resolver):
    user = path_resolver._user_repository.get_by_username("testuser")
    user_path = UserPath(path="test_folder/test_subfolder", owner=user)

    result = path_resolver.folder_from_path(user_path)
    assert result.id == "folder-789"
    assert result.name == "test_subfolder"
    assert len(result.subfolders) == 0


def test_folder_from_path_root_LookupError(path_resolver):
    user = UserEntity(username="other-testuser")
    user_path = UserPath.root_folder_of(user)

    with pytest.raises(LookupError):
        path_resolver.folder_from_path(user_path)


def test_folder_from_path_ResourceNotFound(path_resolver):
    user = path_resolver._user_repository.get_by_username("testuser")
    user_path = UserPath(path="non-existing", owner=user)

    with pytest.raises(ResourceNotFoundException):
        path_resolver.folder_from_path(user_path)


def test_folder_from_path_deep_subfolder_ResourceNotFound(path_resolver):
    user = path_resolver._user_repository.get_by_username("testuser")
    user_path = UserPath(path="test_folder/non-existing", owner=user)

    with pytest.raises(ResourceNotFoundException):
        path_resolver.folder_from_path(user_path)


def test_file_from_path_success(path_resolver):
    user = path_resolver._user_repository.get_by_username("testuser")
    user_path = UserPath(path="test_file", owner=user)

    result = path_resolver.file_from_path(user_path)
    assert result.id == "file-123"
    assert result.name == "test_file"


def test_file_from_path_deep_path_success(path_resolver):
    user = path_resolver._user_repository.get_by_username("testuser")
    user_path = UserPath(path="test_folder/test_subfile", owner=user)

    result = path_resolver.file_from_path(user_path)
    assert result.id == "file-456"
    assert result.name == "test_subfile"


def test_file_from_path_ResourceNotFound(path_resolver):
    user = path_resolver._user_repository.get_by_username("testuser")
    user_path = UserPath(path="non-existing", owner=user)

    with pytest.raises(ResourceNotFoundException):
        path_resolver.file_from_path(user_path)


def test_file_from_path_deep_path_ResourceNotFound(path_resolver):
    user = path_resolver._user_repository.get_by_username("testuser")
    user_path = UserPath(path="test_folder/non-existing", owner=user)

    with pytest.raises(ResourceNotFoundException):
        path_resolver.file_from_path(user_path)


def test_path_from_folder_shallow_hirarchy_success(path_resolver):
    user = path_resolver._user_repository.get_by_username("testuser")
    user_path = UserPath(path="test_folder", owner=user)
    folder = path_resolver.folder_from_path(user_path)

    result = path_resolver.path_from_folder(folder)
    assert result.path == "test_folder"


def test_path_from_folder_deep_hirarchy_success(path_resolver):
    user = path_resolver._user_repository.get_by_username("testuser")
    user_path = UserPath(path="test_folder/test_subfolder", owner=user)
    folder = path_resolver.folder_from_path(user_path)

    result = path_resolver.path_from_folder(folder)
    assert result.path == "test_folder/test_subfolder"


def test_path_from_folder_LookupError(path_resolver):
    user = UserEntity(username="other-testuser")
    folder = FolderEntity(id="some_id", name="some_folder_name", owner=user)

    with pytest.raises(LookupError):
        path_resolver.path_from_folder(folder)
