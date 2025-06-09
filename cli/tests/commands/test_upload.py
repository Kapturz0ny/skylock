"""
Tests for the upload command
"""

import tempfile
import unittest
import os
from unittest.mock import patch
from pathlib import Path
from typer.testing import CliRunner
from httpx import ConnectError
from skylock_cli.cli import app
from skylock_cli.exceptions import api_exceptions
from tests.helpers import mock_test_context, assert_connect_error

from skylock_cli.model.privacy import Privacy

class TestUploadCommand(unittest.TestCase):
    """Test cases for the Upload command"""

    def setUp(self):
        self.runner = CliRunner()

    def test_upload_nonexistent_file(self):
        """Test uploading a nonexistent file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_file_path = Path(temp_dir) / "nonexistent/file.txt"

            result = self.runner.invoke(app, ["upload", str(nonexistent_file_path)])

            self.assertEqual(result.exit_code, 1)
            expected_output = f"File {nonexistent_file_path} does not exist."
            self.assertIn(expected_output, result.output)

    def test_upload_directory(self):
        """Test uploading a directory instead of a file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            directory_path = Path(temp_dir) / "path/to/directory"
            directory_path.mkdir(parents=True, exist_ok=True)

            result = self.runner.invoke(app, ["upload", str(directory_path)])

            self.assertEqual(result.exit_code, 1)
            expected_output = f"{directory_path} is not a file."
            self.assertIn(expected_output, result.output)

    @patch("skylock_cli.model.token.Token.is_expired", return_value=False)
    @patch("skylock_cli.model.token.Token.is_valid", return_value=True)
    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.core.file_operations.file_requests.send_upload_request")
    def test_upload_success(
        self, mock_send, _mock_get_context, _mock_is_valid, _mock_is_expired
    ):
        """Test successful file upload"""
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = temp_file.name
            temp_file_name = os.path.basename(temp_file_path)
            mock_send.return_value = {
                "name": temp_file_name,
                "path": "",
                "size": 10
            }
            result = self.runner.invoke(app, ["upload", temp_file.name])

            self.assertEqual(result.exit_code, 0)
            self.assertIn("Current working directory: /", result.output)
            self.assertIn(
                f"File {temp_file_name} uploaded to . successfully",
                result.output,
            )
            self.assertIn("Visibility: private 🔐", result.output)


    @patch("skylock_cli.model.token.Token.is_expired", return_value=False)
    @patch("skylock_cli.model.token.Token.is_valid", return_value=True)
    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.core.file_operations.file_requests.send_upload_request")
    def test_upload_success_force(
        self, mock_send, _mock_get_context, _mock_is_valid, _mock_is_expired
    ):
        """Test successful file upload"""
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = temp_file.name
            temp_file_name = os.path.basename(temp_file_path)
            mock_send.return_value = {
                "name": temp_file_name,
                "path": "",
                "size": 10
            }
            result = self.runner.invoke(app, ["upload", temp_file.name, "--force"])

            self.assertEqual(result.exit_code, 0)
            self.assertIn("Current working directory: /", result.output)
            self.assertIn(
                f"File {temp_file_name} uploaded to . successfully",
                result.output,
            )
            self.assertIn("Visibility: private 🔐", result.output)

    @patch("skylock_cli.model.token.Token.is_expired", return_value=False)
    @patch("skylock_cli.model.token.Token.is_valid", return_value=True)
    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(Path("/test")),
    )
    @patch("skylock_cli.core.file_operations.file_requests.send_upload_request")
    def test_upload_success_not_to_root(
        self, mock_send, _mock_get_context, _mock_is_valid, _mock_is_expired
    ):
        """Test successful file upload"""
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = temp_file.name
            temp_file_name = os.path.basename(temp_file_path)
            mock_send.return_value = {
                "name": temp_file_name,
                "path": "/test",
                "size": 10
            }
            result = self.runner.invoke(app, ["upload", temp_file.name])

            self.assertEqual(result.exit_code, 0)
            self.assertIn("Current working directory: /test", result.output)
            self.assertIn(
                f"File {temp_file_name} uploaded to /test successfully",
                result.output,
            )
            self.assertIn("Visibility: private 🔐", result.output)

    @patch("skylock_cli.core.file_operations.file_requests.send_upload_request")
    def test_upload_token_expired(self, mock_send):
        """Test the upload command when the token has expired"""
        mock_send.side_effect = api_exceptions.UserUnauthorizedError()

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = temp_file.name
            result = self.runner.invoke(app, ["upload", temp_file_path])

            self.assertEqual(result.exit_code, 1)
            self.assertIn(
                "User is unauthorized. Please login to use this command.", result.output
            )

    @patch("skylock_cli.core.file_operations.file_requests.send_upload_request")
    def test_upload_file_already_exists_no_force(self, mock_send):
        """Test the upload command when the file already exists"""
        mock_send.side_effect = api_exceptions.FileAlreadyExistsError("test_file")

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = temp_file.name
            result = self.runner.invoke(app, ["upload", temp_file_path])

            self.assertEqual(result.exit_code, 1)
            self.assertIn(
                "File `test_file` already exists! Use the --force flag to overwrite it",
                result.output,
            )

    @patch("skylock_cli.core.file_operations.file_requests.send_upload_request")
    def test_upload_file_directory_does_not_exist(self, mock_send):
        """Test the upload command when the directory does not exist"""
        mock_send.side_effect = api_exceptions.DirectoryNotFoundError("/test")

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = temp_file.name
            result = self.runner.invoke(app, ["upload", temp_file_path])

            self.assertEqual(result.exit_code, 1)
            self.assertIn(
                "Directory `/test` does not exist!",
                result.output,
            )

    @patch("skylock_cli.core.file_operations.file_requests.send_upload_request")
    def test_upload_invalid_path(self, mock_send):
        """Test the upload command when the path is invalid"""
        mock_send.side_effect = api_exceptions.InvalidPathError("test_path")

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = temp_file.name
            result = self.runner.invoke(app, ["upload", temp_file_path])

            self.assertEqual(result.exit_code, 1)
            self.assertIn("Invalid path `test_path`", result.output)

    @patch("skylock_cli.core.file_operations.file_requests.send_upload_request")
    def test_upload_api_error(self, mock_send):
        """Test the upload command when an API error occurs"""
        mock_send.side_effect = api_exceptions.SkyLockAPIError("Test error")

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = temp_file.name
            result = self.runner.invoke(app, ["upload", temp_file_path])

            self.assertEqual(result.exit_code, 1)
            self.assertIn("Test error", result.output)

    @patch("skylock_cli.core.file_operations.file_requests.send_upload_request")
    def test_upload_connection_error(self, mock_send):
        """Test the upload command when a ConnectError occurs"""
        mock_send.side_effect = ConnectError("Failed to connect to the server")

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = temp_file.name
            result = self.runner.invoke(app, ["upload", temp_file_path])
            assert_connect_error(result)


if __name__ == "__main__":
    unittest.main()
