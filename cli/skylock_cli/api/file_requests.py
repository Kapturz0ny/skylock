"""
Module to send file requests to the SkyLock backend API.
"""

from urllib.parse import quote
from http import HTTPStatus
from pathlib import Path
from httpx import Client
from typing import Literal

from skylock_cli.config import API_URL, API_HEADERS
from skylock_cli.core.context_manager import ContextManager
from skylock_cli.model.token import Token
from skylock_cli.api import bearer_auth
from skylock_cli.exceptions import api_exceptions
from skylock_cli.utils.cli_exception_handler import handle_standard_errors

client = Client(base_url=ContextManager.get_context().base_url + API_URL)


def send_upload_request(
    token: Token,
    virtual_path: Path,
    files: dict,
    force: bool,
    privacy: Literal["private", "public"] = "private",
) -> dict:
    """
    Send an upload request to the SkyLock backend API.

    Args:
        token (Token): The token object containing authentication token.
        virtual_path (Path): The path where the file should be uploaded.
        files (dict): The file to upload.
    """
    url = "/upload/files" + quote(str(virtual_path))
    auth = bearer_auth.BearerAuth(token)
    params = {"force": force, "privacy": privacy}

    response = client.post(url=url, auth=auth, files=files, params=params)

    standard_error_dict = {
        HTTPStatus.UNAUTHORIZED: api_exceptions.UserUnauthorizedError(),
        HTTPStatus.NOT_FOUND: api_exceptions.DirectoryNotFoundError(
            virtual_path.parent
        ),
        HTTPStatus.BAD_REQUEST: api_exceptions.InvalidPathError(virtual_path),
    }

    handle_standard_errors(standard_error_dict, response.status_code)

    if response.status_code == HTTPStatus.CONFLICT:
        if not force:
            raise api_exceptions.FileAlreadyExistsError(virtual_path)

    if response.status_code != HTTPStatus.CREATED:
        raise api_exceptions.SkyLockAPIError(
            f"Failed to upload file (Error Code: {response.status_code})"
        )

    return response.json()


def send_download_request(token: Token, virtual_path: Path) -> bytes:
    """
    Send a download request to the SkyLock backend API.

    Args:
        token (Token): The token object containing authentication token.
        virtual_path (Path): The path of the file to download.

    Returns:
        bytes: The binary content of the downloaded file.
    """
    url = "/download/files" + quote(str(virtual_path))
    auth = bearer_auth.BearerAuth(token)

    response = client.get(url=url, auth=auth, headers=API_HEADERS)

    standard_error_dict = {
        HTTPStatus.UNAUTHORIZED: api_exceptions.UserUnauthorizedError(),
        HTTPStatus.NOT_FOUND: api_exceptions.FileNotFoundError(virtual_path),
        HTTPStatus.BAD_REQUEST: api_exceptions.InvalidPathError(virtual_path),
    }

    handle_standard_errors(standard_error_dict, response.status_code)

    if response.status_code != HTTPStatus.OK:
        raise api_exceptions.SkyLockAPIError(
            f"Failed to download file (Error Code: {response.status_code})"
        )

    if not response.content:
        raise api_exceptions.InvalidResponseFormatError()

    return response.content


def send_rm_request(token: Token, virtual_path: Path) -> None:
    """
    Send a remove request to the SkyLock backend API.

    Args:
        token (Token): The token object containing authentication token.
        virtual_path (Path): The path of the file to remove.
    """
    url = "/files" + quote(str(virtual_path))
    auth = bearer_auth.BearerAuth(token)

    response = client.delete(url=url, auth=auth, headers=API_HEADERS)

    standard_error_dict = {
        HTTPStatus.UNAUTHORIZED: api_exceptions.UserUnauthorizedError(),
        HTTPStatus.NOT_FOUND: api_exceptions.FileNotFoundError(virtual_path),
        HTTPStatus.BAD_REQUEST: api_exceptions.InvalidPathError(virtual_path),
    }

    handle_standard_errors(standard_error_dict, response.status_code)

    if response.status_code != HTTPStatus.NO_CONTENT:
        raise api_exceptions.SkyLockAPIError(
            f"Failed to remove file (Error Code: {response.status_code})"
        )


def send_change_privacy(
    token: Token,
    virtual_path: Path,
    privacy: Literal["private", "protected", "public"],
    shared_to: list[str] = [],
) -> dict:
    """
    Send a make public request to the SkyLock backend API.

    Args:
        token (Token): The token object containing authentication token.
        virtual_path (Path): The path of the file to be made public.
    """
    url = "/files" + quote(str(virtual_path))
    auth = bearer_auth.BearerAuth(token)
    body = {"privacy": privacy, "shared": shared_to}
    response = client.patch(url=url, auth=auth, headers=API_HEADERS, json=body)

    standard_error_dict = {
        HTTPStatus.UNAUTHORIZED: api_exceptions.UserUnauthorizedError(),
        HTTPStatus.NOT_FOUND: api_exceptions.FileNotFoundError(virtual_path),
    }

    handle_standard_errors(standard_error_dict, response.status_code)

    if response.status_code != HTTPStatus.OK:
        raise api_exceptions.SkyLockAPIError(
            f"Failed to make file public (Error Code: {response.status_code})"
        )

    return response.json()


def send_share_request(token: Token, virtual_path: Path) -> dict:
    """
    Send a share request to the SkyLock backend API.

    Args:
        token (Token): The token object containing authentication token.
        virtual_path (Path): The path of the file to be shared.

    Returns:
        dict: The response from the API.
    """
    url = "/share/files" + quote(str(virtual_path))
    auth = bearer_auth.BearerAuth(token)

    response = client.get(url=url, auth=auth, headers=API_HEADERS)

    standard_error_dict = {
        HTTPStatus.UNAUTHORIZED: api_exceptions.UserUnauthorizedError(),
        HTTPStatus.NOT_FOUND: api_exceptions.FileNotFoundError(virtual_path),
        HTTPStatus.FORBIDDEN: api_exceptions.FileNotPublicError(virtual_path),
    }

    handle_standard_errors(standard_error_dict, response.status_code)

    if response.status_code != HTTPStatus.OK:
        raise api_exceptions.SkyLockAPIError(
            f"Failed to share file (Error Code: {response.status_code})"
        )

    if "location" not in response.json() or not response.json()["location"]:
        raise api_exceptions.InvalidResponseFormatError()

    return response.json()
