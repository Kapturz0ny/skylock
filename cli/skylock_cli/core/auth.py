"""
Module that contains logic for the cli commands related to authentication
"""

from skylock_cli.api.auth_requests import send_login_request, send_register_request, send_verify_code_request
from skylock_cli.utils.cli_exception_handler import CLIExceptionHandler
from skylock_cli.core.context_manager import ContextManager
from skylock_cli.model import user, context, directory, user_with_code
from skylock_cli.config import ROOT_PATH


def register_user(login: str, password: str) -> None:
    """
    Register a new user.

    Args:
        login (str): The username of the new user.
        password (str): The password of the new user.

    Returns:
        None
    """
    _user = user.User(username=login, password=password)
    with CLIExceptionHandler():
        send_register_request(_user)

def verify_code(login: str, password: str, code: str) -> None:
    """
    Verify 2FA code given over email.

    Args:
        login (str): The username of the new user.
        password (str): The password of the new user.
        codde (str): The verification code 

    Returns:
        None
    """
    _user = user_with_code.UserWithCode(username=login, password=password, code=code)
    with CLIExceptionHandler():
        send_verify_code_request(_user)

def login_user(login: str, password: str) -> context.Context:
    """
    Login an existing user.

    Args:
        login (str): The username of the user.
        password (str): The password of the user.

    Returns:
        Token: The token object containing the authentication token.
    """
    _user = user.User(username=login, password=password)
    old_context = ContextManager.get_context()
    with CLIExceptionHandler():
        new_token = send_login_request(_user)

    new_context = context.Context(
        token=new_token,
        cwd=old_context.cwd if old_context.cwd else directory.Directory(path=ROOT_PATH),
        base_url=old_context.base_url,
    )
    ContextManager.save_context(new_context)
    return new_context
