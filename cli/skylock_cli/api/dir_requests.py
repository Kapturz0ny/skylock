"""
Module to send directory requests to the SkyLock backend API.
"""

from urllib.parse import quote
from pathlib import Path
from http import HTTPStatus
from httpx import Client
from skylock_cli.config import API_URL, API_HEADERS
from skylock_cli.core.context_manager import ContextManager
from skylock_cli.exceptions import api_exceptions
from skylock_cli.model.token import Token
from skylock_cli.api import bearer_auth
from skylock_cli.model.privacy import Privacy
from skylock_cli.utils.cli_exception_handler import handle_standard_errors

client = Client(base_url=ContextManager.get_context().base_url + API_URL)


def send_mkdir_request(
    token: Token, path: Path, parent: bool, privacy: Privacy
) -> dict:
    """
    Send a mkdir request to the SkyLock backend API.

    Args:
        token (Token): The token object containing authentication token.
        path (str): The path of the directory to be created.
        parent (bool): If True, create parent directories if they do not exist.
    """
    url = "/folders" + quote(str(path))
    auth = bearer_auth.BearerAuth(token)
    params = {"parent": parent, "privacy": privacy.value}

    response = client.post(url=url, auth=auth, headers=API_HEADERS, params=params)

    standard_error_dict = {
        HTTPStatus.UNAUTHORIZED: api_exceptions.UserUnauthorizedError(),
        HTTPStatus.CONFLICT: api_exceptions.DirectoryAlreadyExistsError(path),
        HTTPStatus.BAD_REQUEST: api_exceptions.InvalidPathError(path),
    }

    handle_standard_errors(standard_error_dict, response.status_code)

    if response.status_code == HTTPStatus.NOT_FOUND:
        if not parent:
            missing = response.json().get("missing", str(path))
            raise api_exceptions.DirectoryMissingError(missing)

    if response.status_code != HTTPStatus.CREATED:
        raise api_exceptions.SkyLockAPIError(
            f"Failed to create directory (Error Code: {response.status_code})"
        )

    return response.json()


def send_rmdir_request(token: Token, path: Path, recursive: bool) -> None:
    """
    Send a rm request to the SkyLock backend API.

    Args:
        token (Token): The token object containing authentication token.
        path (str): The path of the directory to be deleted.
        force (bool): If True, delete the directory recursively.
    """
    url = "/folders" + quote(str(path))
    auth = bearer_auth.BearerAuth(token)
    params = {"recursive": recursive}

    response = client.delete(url=url, auth=auth, headers=API_HEADERS, params=params)

    standard_error_dict = {
        HTTPStatus.UNAUTHORIZED: api_exceptions.UserUnauthorizedError(),
        HTTPStatus.NOT_FOUND: api_exceptions.DirectoryNotFoundError(path),
        HTTPStatus.FORBIDDEN: api_exceptions.SpecialDirectoryDeletionError(path),
    }

    handle_standard_errors(standard_error_dict, response.status_code)

    if response.status_code == HTTPStatus.CONFLICT:
        raise (
            api_exceptions.DirectoryNotEmptyError(path)
            if not recursive
            else api_exceptions.SkyLockAPIError(
                f"Failed to delete directory (Error Code: {response.status_code})"
            )
        )

    if response.status_code != HTTPStatus.NO_CONTENT:
        raise api_exceptions.SkyLockAPIError(
            f"Failed to delete directory (Error Code: {response.status_code})"
        )

def send_change_visibility_request(token: Token, path: Path, privacy: Privacy) -> dict:
    """
    Send a request that changes privacy of the file to the SkyLock backend API.

    Args:
        token (Token): The token object containing authentication token.
        virtual_path (Path): The path of the file to be changed.
        privacy (Privacy enum): The visibility of the file we want to set.
        shared_to (list[str]): If the visibility is set to "Protected", this argument specifies to whom should the file be visible to.
    """

    url = "/folders" + quote(str(path))
    auth = bearer_auth.BearerAuth(token)
    body = {"privacy": privacy.value, "recursive": True}
    response = client.patch(url=url, auth=auth, headers=API_HEADERS, json=body)

    standard_error_dict = {
        HTTPStatus.UNAUTHORIZED: api_exceptions.UserUnauthorizedError(),
        HTTPStatus.NOT_FOUND: api_exceptions.DirectoryNotFoundError(path),
    }

    handle_standard_errors(standard_error_dict, response.status_code)

    if response.status_code != HTTPStatus.OK:
        raise api_exceptions.SkyLockAPIError(
            f"Failed to make folder {privacy.value} (Error Code: {response.status_code})"
        )

    return response.json()


def send_share_request(token: Token, path: Path) -> dict:
    """
    Send a share request to the SkyLock backend API.

    Args:
        token (Token): The token object containing authentication token.
        path (str): The path of the directory to be shared.

    Returns:
        dict: The response from the API.
    """
    url = "/share/folders" + quote(str(path))
    auth = bearer_auth.BearerAuth(token)

    response = client.get(url=url, auth=auth, headers=API_HEADERS)

    standard_error_dict = {
        HTTPStatus.UNAUTHORIZED: api_exceptions.UserUnauthorizedError(),
        HTTPStatus.NOT_FOUND: api_exceptions.DirectoryNotFoundError(path),
        HTTPStatus.FORBIDDEN: api_exceptions.DirectoryNotPublicError(path),
    }

    handle_standard_errors(standard_error_dict, response.status_code)

    if "location" not in response.json() or not response.json()["location"]:
        raise api_exceptions.InvalidResponseFormatError()

    if response.status_code != HTTPStatus.OK:
        raise api_exceptions.SkyLockAPIError(
            f"Failed to share directory (Error Code: {response.status_code})"
        )

    return response.json()


def send_zip_request(token: Token, path: Path, force: bool) -> dict:
    """
    Send a zip request to the SkyLock backend API.

    Args:
        token (Token): The token object containing authentication token.
        path (str): The path of the directory to be ziped.
        force (bool): Flag to overwrite a file <PATH>.zip if the file already exists

    Returns:
        dict: The response from the API.
    """
    url = "/zip" + quote(str(path))
    auth = bearer_auth.BearerAuth(token)
    params = {"force": force}
    zip_path = path.name+".zip"

    standard_error_dict = {
        HTTPStatus.UNAUTHORIZED: api_exceptions.UserUnauthorizedError(),
        HTTPStatus.NOT_FOUND: api_exceptions.DirectoryNotFoundError(path),
        HTTPStatus.FORBIDDEN: api_exceptions.ZipJobStartedError(path),
        HTTPStatus.CONFLICT: api_exceptions.FileAlreadyExistsError(zip_path),
    }

    response = client.post(url=url, auth=auth, headers=API_HEADERS, params=params)

    handle_standard_errors(standard_error_dict, response.status_code)

    if response.status_code != HTTPStatus.CREATED:
        raise api_exceptions.SkyLockAPIError(
            f"Failed to zip directory (Error Code: {response.status_code})"
        )

    return response.json()
