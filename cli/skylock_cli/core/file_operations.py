"""
Module to handle logic for file operations
"""

from pathlib import Path
import os
import tempfile

from pydantic import TypeAdapter
from skylock_cli.utils.cli_exception_handler import CLIExceptionHandler
from skylock_cli.core import path_parser, context_manager
from skylock_cli.model.file import File
from skylock_cli.model.share_link import ShareLink
from skylock_cli.model.privacy import Privacy
from skylock_cli.api import file_requests
from skylock_cli.exceptions.core_exceptions import NotAFileError
from skylock_cli.config import DOWNLOADS_DIR
from skylock_cli.scripts.setup_config import create_downloads_dir


def upload_file(
    real_file_path: Path,
    destination_path: Path,
    force: bool = False,
    privacy: Privacy = Privacy.PRIVATE,
) -> File:
    """Upload a file"""
    current_context = context_manager.ContextManager.get_context()
    with CLIExceptionHandler():
        joind_path = (
            path_parser.parse_path(current_context.cwd.path, destination_path)
            / real_file_path.name
        )

        with open(real_file_path, "rb") as file:
            files = {"file": (real_file_path.name, file)}
            response = file_requests.send_upload_request(
                current_context.token,
                joind_path,
                files,
                force,
                privacy,
            )

        new_file = TypeAdapter(File).validate_python(response)

    return new_file


def download_file(virtual_file_path: Path) -> Path:
    """Download a file"""
    current_context = context_manager.ContextManager.get_context()
    with CLIExceptionHandler():
        joind_path = path_parser.parse_path(current_context.cwd.path, virtual_file_path)

        file_content = file_requests.send_download_request(
            current_context.token, joind_path
        )

        if not DOWNLOADS_DIR.exists():
            create_downloads_dir()

        target_file_path = DOWNLOADS_DIR / joind_path.name
        if target_file_path.exists():
            target_file_path = _generate_unique_file_path(
                DOWNLOADS_DIR, joind_path.name
            )

        with open(target_file_path, "wb") as file:
            file.write(file_content)

    return target_file_path


def remove_file(file_path: str) -> Path:
    """Remove a file"""
    current_context = context_manager.ContextManager.get_context()
    with CLIExceptionHandler():

        if path_parser.is_directory(file_path):
            raise NotAFileError(file_path)

        joind_path = path_parser.parse_path(current_context.cwd.path, file_path)
        file_requests.send_rm_request(current_context.token, joind_path)
    return joind_path


def change_file_visibility(file_path: str, mode: Privacy, shared_to: list[str]) -> File:
    """Change files visibitity to one of [protected, private, public]"""
    current_context = context_manager.ContextManager.get_context()
    with CLIExceptionHandler():
        joind_path = path_parser.parse_path(current_context.cwd.path, Path(file_path))
        response = file_requests.send_change_privacy(
            current_context.token, joind_path, privacy=mode, shared_to=shared_to
        )
        changed_file = TypeAdapter(File).validate_python(response)
    return changed_file


def share_file(file_path: str) -> ShareLink:
    """Share a file"""
    current_context = context_manager.ContextManager.get_context()
    with CLIExceptionHandler():
        joind_path = path_parser.parse_path(current_context.cwd.path, Path(file_path))
        response = file_requests.send_share_request(current_context.token, joind_path)
    return ShareLink(base_url=current_context.base_url, location=response["location"])


def _generate_unique_file_path(directory: Path, file_name: str) -> Path:
    """Generate a unique file path using tempfile.NamedTemporaryFile"""
    base_name, extension = os.path.splitext(file_name)
    with tempfile.NamedTemporaryFile(
        dir=directory, prefix=base_name, suffix=extension, delete=False
    ) as temp_file:
        unique_file_path = Path(temp_file.name)
    return unique_file_path
