"""
Tests for the download command
"""

import unittest
from unittest.mock import patch, mock_open
from pathlib import Path
from typer.testing import CliRunner
from httpx import ConnectError
from skylock_cli.cli import app
from skylock_cli.exceptions import api_exceptions
from tests.helpers import mock_test_context, assert_connect_error


class TestDownloadCommand(unittest.TestCase):
    """Test cases for the download command"""

    def setUp(self):
        self.runner = CliRunner()

    @patch("skylock_cli.core.file_operations.Path.exists", return_value=True)
    @patch(
        "skylock_cli.core.file_operations._generate_unique_file_path",
        return_value=Path("/mocked/Downloads/file.txt"),
    )
    @patch("skylock_cli.core.file_operations.create_downloads_dir", return_value=None)
    @patch("skylock_cli.model.token.Token.is_expired", return_value=False)
    @patch("skylock_cli.model.token.Token.is_valid", return_value=True)
    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch(
        "skylock_cli.core.file_operations.file_requests.send_download_request",
        return_value=None,
    )
    @patch("builtins.open", new_callable=mock_open)
    def test_download_success_target_path_exists(
        self,
        _mock_open,
        _mock_send,
        _mock_get_context,
        _mock_is_valid,
        _mock_is_expired,
        _mock_create_downloads_dir,
        _mock_generate_unique_file_path,
        _mock_exists,
    ):
        """Test successful file download"""
        result = self.runner.invoke(app, ["download", "file.txt"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Current working directory: /", result.output)
        self.assertIn(
            "File file.txt downloaded successfully to /mocked/Downloads", result.output
        )

    @patch(
        "skylock_cli.core.file_operations.DOWNLOADS_DIR", new=Path("/mocked/Downloads/")
    )
    @patch("skylock_cli.core.file_operations.Path.exists", return_value=False)
    @patch("skylock_cli.core.file_operations.create_downloads_dir", return_value=None)
    @patch("skylock_cli.model.token.Token.is_expired", return_value=False)
    @patch("skylock_cli.model.token.Token.is_valid", return_value=True)
    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch(
        "skylock_cli.core.file_operations.file_requests.send_download_request",
        return_value=None,
    )
    @patch("builtins.open", new_callable=mock_open)
    def test_download_success_target_path_not_exists(
        self,
        _mock_open,
        _mock_send,
        _mock_get_context,
        _mock_is_valid,
        _mock_is_expired,
        _mock_create_downloads_dir,
        _mock_exists,
    ):
        """Test successful file download when target path does not exist"""
        result = self.runner.invoke(app, ["download", "file.txt"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Current working directory: /", result.output)
        self.assertIn(
            "File file.txt downloaded successfully to /mocked/Downloads", result.output
        )

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.core.file_operations.file_requests.send_download_request")
    def test_download_token_expired(self, mock_send, _mock_get_context):
        """Test the download command when the token has expired"""
        mock_send.side_effect = api_exceptions.UserUnauthorizedError()
        result = self.runner.invoke(app, ["download", "file.txt"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn(
            "User is unauthorized. Please login to use this command.", result.output
        )

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.core.file_operations.file_requests.send_download_request")
    def test_download_file_not_found(self, mock_send, _mock_get_context):
        """Test the download command when the file is not found"""
        mock_send.side_effect = api_exceptions.FileNotFoundError("file.txt")
        result = self.runner.invoke(app, ["download", "file.txt"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("File `file.txt` does not exist!", result.output)

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.core.file_operations.file_requests.send_download_request")
    def test_download_connection_error(self, mock_send, _mock_get_context):
        """Test the download command when a connection error occurs (server is down)"""
        mock_send.side_effect = ConnectError("Failed to connect to the server")
        result = self.runner.invoke(app, ["download", "file.txt"])
        assert_connect_error(result)

    @patch("skylock_cli.core.file_operations.file_requests.send_download_request")
    def test_download_invalid_path(self, mock_send):
        """Test the download command when the path is invalid"""
        mock_send.side_effect = api_exceptions.InvalidPathError("/$/file.txt")
        result = self.runner.invoke(app, ["download", "/$/file.txt"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Invalid path `/$/file.txt`", result.output)

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.core.file_operations.file_requests.send_download_request")
    def test_download_api_error(self, mock_send, _mock_get_context):
        """Test the download command when an API error occurs"""
        mock_send.side_effect = api_exceptions.SkyLockAPIError(
            "Failed to download file (Error Code: 500)"
        )
        result = self.runner.invoke(app, ["download", "file.txt"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Failed to download file (Error Code: 500)", result.output)


if __name__ == "__main__":
    unittest.main()
