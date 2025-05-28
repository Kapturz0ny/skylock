import pytest
from unittest.mock import MagicMock, patch
from skylock.utils.exceptions import (
    FolderNotEmptyException,
    ForbiddenActionException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    RootFolderAlreadyExistsException,
    UserNotFoundException,
)

from skylock.database.models import FileEntity, FolderEntity, UserEntity, LinkEntity
from skylock.utils.path import UserPath
from skylock.service.resource_service import ResourceService

from skylock.api.models import Privacy, FolderType, ResourceType
from fastapi import HTTPException
from types import SimpleNamespace
from pathlib import Path


def test_get_root_folder_success(resource_service, mock_folder_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath.root_folder_of(user)
    root_folder = FolderEntity(id="folder-456", name=user_path.root_folder_name, owner=user)

    mock_folder_repository.get_by_name_and_parent_id.side_effect = [root_folder]

    result = resource_service.get_folder(user_path)
    assert result == root_folder
    mock_folder_repository.get_by_name_and_parent_id.assert_called_once_with(
        name=root_folder.name, parent_id=None
    )


def test_get_subfolder_success(resource_service, mock_folder_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath(path="test_folder", owner=user)
    root_folder = FolderEntity(id="folder-456", name=user_path.root_folder_name, owner=user)
    subfolder = FolderEntity(id="folder-789", name="test_folder", owner=user)

    mock_folder_repository.get_by_name_and_parent_id.side_effect = [
        root_folder,
        subfolder,
    ]

    result = resource_service.get_folder(user_path)
    assert result == subfolder
    mock_folder_repository.get_by_name_and_parent_id.assert_called()


def test_get_root_folder_nonexistent(resource_service, mock_folder_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath.root_folder_of(user)

    mock_folder_repository.get_by_name_and_parent_id.side_effect = [None]

    with pytest.raises(LookupError):
        resource_service.get_folder(user_path)


def test_get_subfolder_nonexistent(resource_service, mock_folder_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath(path="non-existent", owner=user)
    root_folder = FolderEntity(id="folder-456", name=user_path.root_folder_name, owner=user)

    mock_folder_repository.get_by_name_and_parent_id.side_effect = [root_folder, None]

    with pytest.raises(ResourceNotFoundException):
        resource_service.get_folder(user_path)


def test_create_folder_success(resource_service, mock_folder_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath("subfolder", user)
    root_folder = FolderEntity(id="folder-root", name=user_path.root_folder_name, owner=user)

    mock_folder_repository.get_by_name_and_parent_id.side_effect = [root_folder]

    resource_service.create_folder(user_path)
    mock_folder_repository.save.assert_called_once()


def test_create_folder_root_forbidden(resource_service):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath.root_folder_of(user)

    with pytest.raises(ForbiddenActionException):
        resource_service.create_folder(user_path)


def test_create_folder_duplicate_name(resource_service, mock_folder_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath("subfolder", user)
    root_folder = FolderEntity(id="folder-root", name=user_path.root_folder_name, owner=user)
    existing_folder = FolderEntity(id="folder-456", name="subfolder", parent_folder=root_folder)

    mock_folder_repository.get_by_name_and_parent_id.side_effect = [root_folder]

    with pytest.raises(ResourceAlreadyExistsException):
        resource_service.create_folder(user_path)


def test_delete_folder_success(resource_service, mock_folder_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath("subfolder", user)
    root_folder = FolderEntity(id="folder-root", name=user_path.root_folder_name, owner=user)
    subfolder = FolderEntity(id="folder-456", name="subfolder", parent_folder_id=root_folder.id)

    mock_folder_repository.get_by_name_and_parent_id.side_effect = [
        root_folder,
        subfolder,
    ]

    resource_service.delete_folder(user_path)
    mock_folder_repository.delete.assert_called_once_with(subfolder)


def test_delete_folder_not_empty(resource_service, mock_folder_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath("subfolder", user)
    root_folder = FolderEntity(id="folder-root", name=user_path.root_folder_name, owner=user)
    subfolder = FolderEntity(id="folder-456", name="subfolder", parent_folder_id=root_folder.id)
    sub_subfolder = FolderEntity(
        id="folder-789", name="sub_subfolder", parent_folder_id=subfolder.id
    )
    subfolder.subfolders.append(sub_subfolder)

    mock_folder_repository.get_by_name_and_parent_id.side_effect = [
        root_folder,
        subfolder,
    ]

    with pytest.raises(FolderNotEmptyException):
        resource_service.delete_folder(user_path, is_recursively=False)


def test_delete_folder_recursive_calls_file_deletion(
    resource_service, mock_folder_repository, mock_file_repository
):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath("parent_folder", user)
    root_folder = FolderEntity(id="folder-root", name=user_path.root_folder_name, owner=user)
    parent_folder = FolderEntity(
        id="folder-123", name="parent_folder", parent_folder_id=root_folder.id
    )
    subfolder = FolderEntity(id="folder-456", name="subfolder", parent_folder_id=parent_folder.id)
    file_in_subfolder = MagicMock()

    parent_folder.subfolders.append(subfolder)
    subfolder.files.append(file_in_subfolder)
    mock_folder_repository.get_by_name_and_parent_id.side_effect = [
        root_folder,
        parent_folder,
    ]

    with patch.object(resource_service, "_delete_file_data") as mock_delete_file_data, patch.object(
        resource_service, "_delete_folder", wraps=resource_service._delete_folder
    ):
        resource_service.delete_folder(user_path, is_recursively=True)

        mock_delete_file_data.assert_called_once_with(file_in_subfolder)
        resource_service._delete_folder.assert_called_with(subfolder, is_recursively=True)
        mock_file_repository.delete.assert_called_once_with(file_in_subfolder)
        mock_folder_repository.delete.assert_any_call(subfolder)
        mock_folder_repository.delete.assert_any_call(parent_folder)


def test_delete_folder_forbidden_root(resource_service):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath.root_folder_of(user)

    with pytest.raises(ForbiddenActionException):
        resource_service.delete_folder(user_path)


def test_create_file_success(resource_service, mock_folder_repository, mock_file_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath("subfolder/file.txt", user)
    root_folder = FolderEntity(id="folder-root", name=user_path.root_folder_name, owner=user)
    subfolder = FolderEntity(
        id="folder-123", name="subfolder", parent_folder_id=root_folder.id, type=FolderType.NORMAL
    )

    mock_folder_repository.get_by_name_and_parent_id.side_effect = [
        root_folder,
        subfolder,
    ]

    with patch.object(resource_service, "_save_file_data") as mock_save_file_data:
        resource_service.create_file(user_path, data=b"file content", size=10)
        mock_save_file_data.assert_called_once()
        mock_file_repository.save.assert_called_once()


def test_create_file_with_duplicate_name(resource_service, mock_folder_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath("subfolder/existing_file.txt", user)
    root_folder = FolderEntity(id="folder-root", name=user_path.root_folder_name, owner=user)
    subfolder = FolderEntity(
        id="folder-123", name="subfolder", parent_folder_id=root_folder.id, type=FolderType.NORMAL
    )
    existing_file = FileEntity(id="file-123", name="existing_file.txt", owner=user, size=10)

    subfolder.files.append(existing_file)

    mock_folder_repository.get_by_name_and_parent_id.side_effect = [
        root_folder,
        subfolder,
    ]

    with pytest.raises(ResourceAlreadyExistsException):
        resource_service.create_file(user_path, data=b"file content", size=10)


def test_get_file_not_found(resource_service, mock_file_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath("nonexistent/file.txt", user)
    mock_file_repository.get_by_name_and_parent.return_value = None

    with pytest.raises(ResourceNotFoundException):
        resource_service.get_file(user_path)


def test_create_file_empty_name_forbidden(resource_service):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath("", user)

    with pytest.raises(ForbiddenActionException):
        resource_service.create_file(user_path, data=b"file content", size=10)


def test_delete_file_success(resource_service, mock_file_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath("subfolder/file.txt", user)
    file = MagicMock()
    file.owner_id = user.id

    mock_file_repository.get_by_name_and_parent.return_value = file

    with patch.object(resource_service, "_delete_file_data") as mock_delete_file_data:
        resource_service.delete_file(user_path)
        mock_delete_file_data.assert_called_once_with(file)
        mock_file_repository.delete.assert_called_once_with(file)


def test_create_root_folder_success(resource_service, mock_folder_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath.root_folder_of(user)

    mock_folder_repository.get_by_name_and_parent_id.side_effect = [None]

    resource_service.create_root_folder(user_path)
    mock_folder_repository.save.assert_called_once()


def test_create_root_folder_not_root(resource_service, mock_folder_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath(path="subfolder", owner=user)

    mock_folder_repository.get_by_name_and_parent_id.side_effect = [None]

    with pytest.raises(ValueError):
        resource_service.create_root_folder(user_path)


def test_create_root_folder_duplicate(resource_service, mock_folder_repository):
    user = UserEntity(id="user-123", username="testuser")
    user_path = UserPath.root_folder_of(user)
    existing_root_folder = FolderEntity(name=user.id, owner=user)

    mock_folder_repository.get_by_name_and_parent_id.return_value = existing_root_folder

    with pytest.raises(RootFolderAlreadyExistsException):
        resource_service.create_root_folder(user_path)


def test_get_folder_by_id(resource_service):
    folder_id = "folder-123"
    folder = FolderEntity(id=folder_id, name="test_folder")
    resource_service._folder_repository.get_by_id.return_value = folder

    result = resource_service.get_folder_by_id(folder_id)

    assert result == folder
    resource_service._folder_repository.get_by_id.assert_called_once_with(folder_id)


def test_get_folder_by_id_no_folder(resource_service):
    folder_id = "folder-123"
    resource_service._folder_repository.get_by_id.return_value = None

    with pytest.raises(ResourceNotFoundException):
        resource_service.get_folder_by_id(folder_id)


def test_get_public_folder(resource_service):
    folder_id = "folder-123"
    folder = FolderEntity(id=folder_id, name="test_folder", privacy=Privacy.PUBLIC)
    resource_service._folder_repository.get_by_id.return_value = folder

    result = resource_service.get_public_folder(folder_id)

    assert result == folder
    resource_service._folder_repository.get_by_id.assert_called_once_with(folder_id)


def test_get_public_folder_not_public(resource_service):
    folder_id = "folder-123"
    folder = FolderEntity(id=folder_id, name="test_folder", privacy=Privacy.PRIVATE)
    resource_service._folder_repository.get_by_id.return_value = folder

    with pytest.raises(ForbiddenActionException):
        resource_service.get_public_folder(folder_id)


def test_get_file_by_id(resource_service):
    file_id = "file-123"
    file = FileEntity(id=file_id, name="test_file", size=10)
    resource_service._file_repository.get_by_id.return_value = file

    result = resource_service.get_file_by_id(file_id)

    assert result == file
    resource_service._file_repository.get_by_id.assert_called_once_with(file_id)


def test_get_file_by_id_no_file(resource_service):
    file_id = "file-123"
    resource_service._file_repository.get_by_id.return_value = None

    with pytest.raises(ResourceNotFoundException):
        resource_service.get_file_by_id(file_id)


def test_get_verified_file_public(resource_service):
    file_id = "file-123"
    file = FileEntity(id=file_id, name="test_file", privacy=Privacy.PUBLIC, size=10)

    resource_service._file_repository.get_by_id.return_value = file
    token = "Bearer valid_token"

    result = resource_service.get_verified_file(file_id, token)
    assert result == file
    resource_service._file_repository.get_by_id.assert_called_once_with(file_id)


def test_get_verified_file_private(resource_service):
    file_id = "file-123"
    file = FileEntity(
        id=file_id, name="test_file", privacy=Privacy.PRIVATE, owner_id="user-123", size=10
    )

    resource_service._file_repository.get_by_id.return_value = file

    token = "Bearer valid_token"
    user = UserEntity(id="user-123", username="testuser")

    with patch(
        "skylock.service.resource_service.get_user_from_jwt",
        return_value=user,
    ):
        result = resource_service.get_verified_file(file_id, token)
        assert result == file
        resource_service._file_repository.get_by_id.assert_called_once_with(file_id)


def test_get_verified_file_private_not_owner(resource_service):
    file_id = "file-123"
    file = FileEntity(
        id=file_id, name="test_file", privacy=Privacy.PRIVATE, owner_id="user-123", size=10
    )

    resource_service._file_repository.get_by_id.return_value = file

    token = "Bearer valid_token"
    user = UserEntity(id="user-456", username="testuser")

    with patch(
        "skylock.service.resource_service.get_user_from_jwt",
        return_value=user,
    ):
        with pytest.raises(ForbiddenActionException):
            resource_service.get_verified_file(file_id, token)


def test_get_verified_file_protected(resource_service):
    file_id = "file-123"
    file = FileEntity(
        id=file_id, name="test_file", privacy=Privacy.PROTECTED, owner_id="user-123", size=10
    )
    file.shared_to = ["testuser"]

    resource_service._file_repository.get_by_id.return_value = file

    token = "Bearer valid_token"
    user = UserEntity(id="user-456", username="testuser")

    with patch(
        "skylock.service.resource_service.get_user_from_jwt",
        return_value=user,
    ):
        result = resource_service.get_verified_file(file_id, token)
        assert result == file
        resource_service._file_repository.get_by_id.assert_called_once_with(file_id)


def test_get_verified_file_protected_not_shared(resource_service):
    file_id = "file-123"
    file = FileEntity(
        id=file_id, name="test_file", privacy=Privacy.PROTECTED, owner_id="user-123", size=10
    )
    file.shared_to = ["someone"]

    resource_service._file_repository.get_by_id.return_value = file

    token = "Bearer valid_token"
    user = UserEntity(id="user-789", username="testuser")

    with patch(
        "skylock.service.resource_service.get_user_from_jwt",
        return_value=user,
    ):
        with pytest.raises(ForbiddenActionException):
            resource_service.get_verified_file(file_id, token)


def test_get_verified_file_protected_owner(resource_service):
    file_id = "file-123"
    file = FileEntity(
        id=file_id, name="test_file", privacy=Privacy.PROTECTED, owner_id="user-123", size=10
    )
    file.shared_to = ["user-456"]

    resource_service._file_repository.get_by_id.return_value = file

    token = "Bearer valid_token"
    user = UserEntity(id="user-123", username="testuser")

    with patch(
        "skylock.service.resource_service.get_user_from_jwt",
        return_value=user,
    ):
        result = resource_service.get_verified_file(file_id, token)
        assert result == file
        resource_service._file_repository.get_by_id.assert_called_once_with(file_id)


def test_get_verified_file_invalid_token(resource_service):
    file_id = "file-123"
    file = FileEntity(id=file_id, name="test_file", privacy=Privacy.PRIVATE, size=10)

    resource_service._file_repository.get_by_id.return_value = file
    token = "Bearer invalid_token"
    user = UserEntity(id="user-123", username="testuser")

    with patch(
        "skylock.service.resource_service.get_user_from_jwt",
        side_effect=HTTPException(status_code=403),
    ):
        with pytest.raises(ForbiddenActionException):
            resource_service.get_verified_file(file_id, token)


def test_get_file_by_token_path_no_token(resource_service):
    with pytest.raises(ForbiddenActionException) as exc_info:
        resource_service.get_file_by_token_path("path")

    assert str(exc_info.value) == "Authentication token is required for this resource."


def test_get_file_by_token_path_invalid_token(resource_service):
    with patch(
        "skylock.service.resource_service.get_user_from_jwt", side_effect=HTTPException(404)
    ):
        with pytest.raises(ForbiddenActionException) as exc_info:
            resource_service.get_file_by_token_path("path", "token")

    assert str(exc_info.value) == "Invalid token"


@patch("skylock.service.resource_service.get_user_from_jwt")
@patch("skylock.service.resource_service.ResourceService.check_resource_type")
@patch("skylock.service.resource_service.ResourceService.get_file")
def test_get_file_by_token_path_file(
    mock_get_file, mock_resource_type, mock_user_from_jwt, resource_service
):
    user = UserEntity(id="user-789", username="testuser")
    mock_user_from_jwt.return_value = user

    mock_resource_type.return_value = ResourceType.FILE

    file = FileEntity(
        id="123", name="test_file", privacy=Privacy.PRIVATE, owner_id="user-123", size=10
    )

    mock_get_file.return_value = file

    assert resource_service.get_file_by_token_path("path", "token") == file


@patch("skylock.service.resource_service.get_user_from_jwt")
@patch("skylock.service.resource_service.ResourceService.check_resource_type")
@patch("skylock.service.resource_service.ResourceService.get_link")
def test_get_file_by_token_path_link_file(
    mock_get_link, mock_resource_type, mock_user_from_jwt, resource_service
):
    user = UserEntity(id="user-789", username="testuser")
    mock_user_from_jwt.return_value = user

    mock_resource_type.return_value = ResourceType.LINK

    file = FileEntity(
        id="123", name="test_file", privacy=Privacy.PRIVATE, owner_id="user-123", size=10
    )
    link = LinkEntity(
        name="link_name", folder_id=1, owner_id=2, resource_type=ResourceType.FILE, target_file=file
    )

    mock_get_link.return_value = link

    assert resource_service.get_file_by_token_path("path", "token") == file


@patch("skylock.service.resource_service.get_user_from_jwt")
@patch("skylock.service.resource_service.ResourceService.check_resource_type")
@patch("skylock.service.resource_service.ResourceService.get_link")
def test_get_file_by_token_path_link_other_type(
    mock_get_link, mock_resource_type, mock_user_from_jwt, resource_service
):
    user = UserEntity(id="user-789", username="testuser")
    mock_user_from_jwt.return_value = user

    mock_resource_type.return_value = ResourceType.LINK

    link = LinkEntity(name="link_name", folder_id=1, owner_id=2, resource_type=ResourceType.FOLDER)

    mock_get_link.return_value = link

    with pytest.raises(ResourceNotFoundException):
        resource_service.get_file_by_token_path("path", "token")


@patch("skylock.service.resource_service.get_user_from_jwt")
@patch("skylock.service.resource_service.ResourceService.check_resource_type")
@patch("skylock.service.resource_service.ResourceService.get_link")
def test_get_file_by_token_path_other(
    mock_get_link, mock_resource_type, mock_user_from_jwt, resource_service
):
    user = UserEntity(id="user-789", username="testuser")
    mock_user_from_jwt.return_value = user

    mock_resource_type.return_value = ResourceType.FOLDER

    with pytest.raises(ResourceNotFoundException):
        resource_service.get_file_by_token_path("path", "token")


@patch("skylock.service.resource_service.get_user_from_jwt")
@patch("skylock.service.resource_service.ResourceService.check_resource_type")
@patch("skylock.service.resource_service.ResourceService.get_link")
def test_get_file_by_token_path_link_file_no_target(
    mock_get_link, mock_resource_type, mock_user_from_jwt, resource_service
):
    user = UserEntity(id="user-789", username="testuser")
    mock_user_from_jwt.return_value = user

    mock_resource_type.return_value = ResourceType.LINK

    link = LinkEntity(
        name="link_name", folder_id=1, owner_id=2, resource_type=ResourceType.FILE, target_file=None
    )

    mock_get_link.return_value = link

    with pytest.raises(ResourceNotFoundException):
        resource_service.get_file_by_token_path("path", "token")


@patch("skylock.service.resource_service.ResourceService.get_file_by_id")
def test_potential_file_import_owner(mock_get_file_by_id, resource_service):
    file = FileEntity(
        id="123", name="test_file", privacy=Privacy.PRIVATE, owner_id="user-123", size=10
    )
    mock_get_file_by_id.return_value = file

    assert resource_service.potential_file_import("user-123", "file_id") == None


@patch.object(ResourceService, "get_file_by_id")
def test_potential_file_import_file_shared_no_user(mock_get_user_by_id, resource_service):
    file = FileEntity(
        id="123", name="test_file", privacy=Privacy.PRIVATE, owner_id="user-123", size=10
    )

    mock_get_user_by_id.return_value = file
    resource_service._shared_file_repository.is_file_shared_to_user.return_value = False
    resource_service._user_repository.get_by_id.return_value = None

    with pytest.raises(UserNotFoundException):
        resource_service.potential_file_import("1", "2")


@patch.object(ResourceService, "get_file_by_id")
@patch.object(UserPath, "root_folder_of")
@patch.object(ResourceService, "get_folder")
@patch.object(ResourceService, "create_link_to_file")
def test_potential_file_import_file_existing_folder_creating_file(
    mock_create_link_to_file, mock_get_folder, mock_root_folder_of, mock_get_user_by_id, resource_service
):

    user = UserEntity(id="user-789", username="testuser")
    file = FileEntity(
        id="123",
        name="test_file",
        privacy=Privacy.PRIVATE,
        owner_id="user-123",
        size=10,
        owner=user,
    )

    mock_get_user_by_id.return_value = file
    resource_service._shared_file_repository.is_file_shared_to_user.return_value = False
    resource_service._user_repository.get_by_id.return_value = user

    mock_root_folder_of.return_value = UserPath("/home", user)

    resource_service.potential_file_import("1", 2)

    mock_get_folder.assert_called_once_with(UserPath("/home/Shared/testuser", user))
    mock_create_link_to_file.assert_called_once_with(UserPath("/home/Shared/testuser/test_file", user), file)

@patch.object(ResourceService, "get_file_by_id")
@patch.object(UserPath, "root_folder_of")
@patch.object(ResourceService, "get_folder")
@patch.object(ResourceService, "create_link_to_file")
@patch.object(ResourceService, "create_folder")
def test_potential_file_import_file_shared_no_existing_folder(
    mock_create_folder, mock_create_link_to_file, mock_get_folder, mock_root_folder_of, mock_get_user_by_id, resource_service
):

    user = UserEntity(id="user-789", username="testuser")
    file = FileEntity(
        id="123",
        name="test_file",
        privacy=Privacy.PRIVATE,
        owner_id="user-123",
        size=10,
        owner=user,
    )

    mock_get_user_by_id.return_value = file
    resource_service._shared_file_repository.is_file_shared_to_user.return_value = False
    resource_service._user_repository.get_by_id.return_value = user

    mock_root_folder_of.return_value = UserPath("/home", user)
    mock_get_folder.side_effect = ResourceNotFoundException("hi")

    resource_service.potential_file_import("1", 2)

    mock_create_folder.assert_called_once_with(
        UserPath("/home/Shared/testuser", user), Privacy.PRIVATE, FolderType.SHARING_USER
    )
    mock_create_link_to_file.assert_called_once_with(UserPath("/home/Shared/testuser/test_file", user), file)


@patch.object(ResourceService, "get_file_by_id")
@patch.object(UserPath, "root_folder_of")
@patch.object(ResourceService, "get_folder")
@patch.object(ResourceService, "create_link_to_file")
def test_potential_file_import_file_existing_folder_file_already_exists(
    mock_create_link_to_file, mock_get_folder, mock_root_folder_of, mock_get_user_by_id, resource_service
):

    user = UserEntity(id="user-789", username="testuser")
    file = FileEntity(
        id="123",
        name="test_file",
        privacy=Privacy.PRIVATE,
        owner_id="user-123",
        size=10,
        owner=user,
    )

    mock_get_user_by_id.return_value = file
    resource_service._shared_file_repository.is_file_shared_to_user.return_value = False
    resource_service._user_repository.get_by_id.return_value = user

    mock_root_folder_of.return_value = UserPath("/home", user)
    mock_create_link_to_file.side_effect = ResourceAlreadyExistsException()

    assert resource_service.potential_file_import("1", 2) == None

    mock_get_folder.assert_called_once_with(UserPath("/home/Shared/testuser", user))