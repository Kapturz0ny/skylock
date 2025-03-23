"""
Module to handle HTTP requests to API
"""

from http import HTTPStatus
from httpx import Client
from skylock_cli.core.context_manager import ContextManager
from skylock_cli.config import API_HEADERS, API_URL
from skylock_cli.model import user, token, user_with_code
from skylock_cli.exceptions import api_exceptions
from skylock_cli.utils.cli_exception_handler import handle_standard_errors

client = Client(base_url=ContextManager.get_context().base_url + API_URL)


def send_register_request(_user: user.User) -> None:
    """
    Send a register request to the SkyLock backend API.

    Args:
        user (User): The user object containing registration details.

    Raises:
        UserAlreadyExistsError: If the user already exists.
        SkyLockAPIError: If there is an error during registration.
    """
    url = "/auth/register"

    response = client.post(url, json=_user.model_dump(), headers=API_HEADERS)

    standard_error_dict = {
        HTTPStatus.CONFLICT: api_exceptions.UserAlreadyExistsError(_user.username)
    }

    handle_standard_errors(standard_error_dict, response.status_code)

    if response.status_code != HTTPStatus.CREATED:
        raise api_exceptions.SkyLockAPIError(
            f"Failed to register user (Error Code: {response.status_code})"
        )


def send_verify_code_request(_user: user_with_code.UserWithCode) -> None:
    """
    Send a code verification request to the SkyLock backend API.

    Args:
        user (User): The user object containing registration details.

    Raises:
        UserAlreadyExistsError: If the user already exists.
        SkyLockAPIError: If there is an error during registration.
    """
    url = "/auth/2FA"

    response = client.post(url, json=_user.model_dump(), headers=API_HEADERS)

    standard_error_dict = {
        HTTPStatus.CONFLICT: api_exceptions.UserAlreadyExistsError(_user.username)
    }

    handle_standard_errors(standard_error_dict, response.status_code)

    if response.status_code != HTTPStatus.CREATED:
        raise api_exceptions.SkyLockAPIError(
            f"Failed to register user (Error Code: {response.status_code})"
        )


def send_login_request(_user: user.User) -> token.Token:
    """
    Send a login request to the SkyLock backend API.

    Args:
        user (User): The user object containing login details.

    Raises:
        AuthenticationError: If the authentication fails.
        SkyLockAPIError: If there is an error during login.
        TokenNotFoundError: If the token is not found in the response.

    Returns:
        Token: The token object containing authentication token.
    """
    url = "/auth/login"

    response = client.post(url, json=_user.model_dump(), headers=API_HEADERS)

    standard_error_dict = {
        HTTPStatus.UNAUTHORIZED: api_exceptions.AuthenticationError()
    }

    handle_standard_errors(standard_error_dict, response.status_code)

    if response.status_code != HTTPStatus.OK:
        raise api_exceptions.SkyLockAPIError(
            f"Failed to login user (Error Code: {response.status_code})"
        )

    token_data = response.json()
    if not token_data:
        raise api_exceptions.TokenNotFoundError()

    return token.Token(**token_data)
