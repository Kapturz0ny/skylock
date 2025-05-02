"""
Module for navigating the file system.
"""

from pathlib import Path
from pydantic import TypeAdapter
from skylock_cli.core import context_manager, path_parser
from skylock_cli.utils.cli_exception_handler import CLIExceptionHandler
from skylock_cli.api.nav_requests import send_ls_request, send_cd_request
from skylock_cli.model import directory, file, resource, link
from skylock_cli.exceptions.core_exceptions import (
    UserTokenExpiredError,
    InvalidUserTokenError,
)


def list_directory(
    directory_path: Path,
) -> tuple[list[resource.Resource], Path]:
    """
    List the contents of a directory.
    """
    current_context = context_manager.ContextManager.get_context()
    with CLIExceptionHandler():
        joind_path = path_parser.parse_path(current_context.cwd.path, directory_path)
        response = send_ls_request(current_context.token, joind_path)
        files = TypeAdapter(list[file.File]).validate_python(response["files"])
        directories = TypeAdapter(list[directory.Directory]).validate_python(
            response["folders"]
        )
        links = TypeAdapter(list[link.Link]).validate_python(response["links"])
    return (sorted(files + directories + links, key=lambda x: x.name), joind_path)


def change_directory(directory_path: Path) -> Path:
    """
    Change the current working directory.
    """
    current_context = context_manager.ContextManager.get_context()
    with CLIExceptionHandler():
        joind_path = path_parser.parse_path(current_context.cwd.path, directory_path)
        send_cd_request(current_context.token, joind_path)
    current_context.cwd = directory.Directory(path=joind_path, name=joind_path.name)
    context_manager.ContextManager.save_context(current_context)
    return joind_path


def get_working_directory() -> directory.Directory:
    """
    Get the current working directory.
    """
    current_context = context_manager.ContextManager.get_context()
    with CLIExceptionHandler():
        if not current_context.token.is_valid():
            raise InvalidUserTokenError()
        if current_context.token.is_expired():
            raise UserTokenExpiredError()
    return current_context.cwd
