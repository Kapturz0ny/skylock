"""
Tests for the ls command
"""

import unittest
from unittest.mock import patch
from typer.testing import CliRunner
from httpx import ConnectError
from skylock_cli.cli import app
from skylock_cli.exceptions import api_exceptions
from tests.helpers import assert_connect_error, mock_test_context

from skylock_cli.model.privacy import Privacy


class TestLSCommand(unittest.TestCase):
    """Test cases for the ls command"""

    def setUp(self):
        self.runner = CliRunner()

    @patch("skylock_cli.model.token.Token.is_expired", return_value=False)
    @patch("skylock_cli.model.token.Token.is_valid", return_value=True)
    @patch("skylock_cli.core.nav.send_ls_request")
    @patch("skylock_cli.core.context_manager.ContextManager.get_context")
    def test_ls_success(
        self, mock_get_context, mock_send, _mock_is_valid, _mock_is_expired
    ):
        """Test the ls command"""
        mock_get_context.return_value = mock_test_context()

        mock_files = [
            {"name": "file2.txt", "path": "/file2.txt", "size": 10, "privacy": Privacy.PUBLIC },
            {"name": "file1.txt", "path": "/file1.txt", "size": 20, "privacy": Privacy.PROTECTED },
        ]
        mock_folders = [
            {"name": "folder1", "path": "/folder1"},
            {"name": "folder2", "path": "/folder2"},
        ]

        mock_send.return_value = {"files": mock_files, "folders": mock_folders, "links": []}

        result = self.runner.invoke(app, ["ls"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Contents of /", result.output)
        self.assertIn("file1.txt  file2.txt  folder1/  folder2/", result.output)

    @patch("skylock_cli.model.token.Token.is_expired", return_value=False)
    @patch("skylock_cli.model.token.Token.is_valid", return_value=True)
    @patch("skylock_cli.core.nav.send_ls_request")
    @patch("skylock_cli.core.context_manager.ContextManager.get_context")
    def test_ls_long_success(
        self, mock_get_context, mock_send, _mock_is_valid, _mock_is_expired
    ):
        """Test the ls command"""
        mock_get_context.return_value = mock_test_context()

        mock_files = [
            {"name": "file1.txt", "path": "/file1.txt", "size": 10, "privacy": Privacy.PRIVATE },
            {"name": "file2.txt", "path": "/file2.txt", "size": 2975, "privacy": Privacy.PROTECTED },
            {"name": "file3.txt", "path": "/file3.txt", "size": 1234913, "privacy": Privacy.PUBLIC },
        ]
        mock_folders = [
            {"name": "folder1", "path": "/folder1", "privacy" : Privacy.PUBLIC},
            {"name": "folder2", "path": "/folder2", "privacy" : Privacy.PRIVATE},
        ]

        mock_send.return_value = {"files": mock_files, "folders": mock_folders, "links": []}

        result = self.runner.invoke(app, ["ls", "-l"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Contents of /", result.output)
        self.assertIn(
            "│ file      │ file1.txt │ /file1.txt │ private 🔐      │ 10 B", result.output
        )
        self.assertIn(
            "│ file      │ file2.txt │ /file2.txt │ protected 🔐/🔒 │ 2.9 kB", result.output
        )
        self.assertIn(
            "│ file      │ file3.txt │ /file3.txt │ public 🔓       │ 1.2 MB", result.output
        )
        self.assertIn(
            "│ directory │ folder1/  │ /folder1   │ public 🔓       │", result.output
        )
        self.assertIn(
            "│ directory │ folder2/  │ /folder2   │ private 🔐      │", result.output
        )

    @patch("skylock_cli.model.token.Token.is_expired", return_value=False)
    @patch("skylock_cli.model.token.Token.is_valid", return_value=True)
    @patch("skylock_cli.core.nav.send_ls_request")
    @patch("skylock_cli.core.context_manager.ContextManager.get_context")
    def test_ls_success_empty(
        self, mock_get_context, mock_send, _mock_is_valid, _mock_is_expired
    ):
        """Test the ls command"""
        mock_get_context.return_value = mock_test_context()

        mock_send.return_value = {"files": [], "folders": [], "links": []}

        result = self.runner.invoke(app, ["ls"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Contents of /", result.output)
        self.assertIn("No contents in directory", result.output)

    @patch("skylock_cli.model.token.Token.is_expired", return_value=False)
    @patch("skylock_cli.model.token.Token.is_valid", return_value=True)
    @patch("skylock_cli.core.nav.send_ls_request")
    @patch("skylock_cli.core.context_manager.ContextManager.get_context")
    def test_ls_success_only_files(
        self, mock_get_context, mock_send, _mock_is_valid, _mock_is_expired
    ):
        """Test the ls command"""
        mock_get_context.return_value = mock_test_context()

        mock_files = [
            {"name": "file1.txt", "path": "/test/file1.txt", "size": 10},
            {"name": "file2.txt", "path": "/test/file2.txt", "size": 20},
        ]
        mock_folders = []

        mock_send.return_value = {"files": mock_files, "folders": mock_folders, "links": []}

        result = self.runner.invoke(app, ["ls", "/test"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Contents of /test", result.output)
        self.assertIn("file1.txt  file2.txt", result.output)

    @patch("skylock_cli.model.token.Token.is_expired", return_value=False)
    @patch("skylock_cli.model.token.Token.is_valid", return_value=True)
    @patch("skylock_cli.core.nav.send_ls_request")
    @patch("skylock_cli.core.context_manager.ContextManager.get_context")
    def test_ls_success_only_folders(
        self, mock_get_context, mock_send, _mock_is_valid, _mock_is_expired
    ):
        """Test the ls command"""
        mock_get_context.return_value = mock_test_context()

        mock_files = []
        mock_folders = [
            {"name": "folder1", "path": "/folder1"},
            {"name": "folder2", "path": "/folder2"},
        ]

        mock_send.return_value = {"files": mock_files, "folders": mock_folders, "links": []}

        result = self.runner.invoke(app, ["ls"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Contents of /", result.output)
        self.assertIn("folder1/  folder2/", result.output)

    @patch("skylock_cli.core.nav.send_ls_request")
    def test_ls_user_unathorized(self, mock_send):
        """Test the ls command when the user is unauthorized"""
        mock_send.side_effect = api_exceptions.UserUnauthorizedError()

        result = self.runner.invoke(app, ["ls"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn(
            "User is unauthorized. Please login to use this command.", result.output
        )

    @patch("skylock_cli.core.nav.send_ls_request")
    def test_ls_skylock_api_error(self, mock_send):
        """Test the ls command when a SkyLockAPIError occurs"""
        mock_send.side_effect = api_exceptions.SkyLockAPIError(
            "An unexpected API error occurred"
        )

        result = self.runner.invoke(app, ["ls"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("An unexpected API error occurred", result.output)

    @patch("skylock_cli.core.nav.send_ls_request")
    def test_ls_connection_error(self, mock_send):
        """Test the ls command when ConnectError occurs (backend is offline)"""
        mock_send.side_effect = ConnectError("Failed to connect to the server")
        result = self.runner.invoke(app, ["ls"])
        assert_connect_error(result)

    @patch("skylock_cli.core.nav.send_ls_request")
    def test_ls_directory_not_found(self, mock_send):
        """Test the ls command when a DirectoryNotFoundError occurs"""
        mock_send.side_effect = api_exceptions.DirectoryNotFoundError("/test")

        result = self.runner.invoke(app, ["ls", "/test"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Directory `/test` does not exist!", result.output)

    @patch("skylock_cli.core.nav.send_ls_request")
    def test_ls_invalid_response_format(self, mock_send):
        """Test the ls command when an InvalidResponseFormatError occurs"""
        mock_send.side_effect = api_exceptions.InvalidResponseFormatError()

        result = self.runner.invoke(app, ["ls"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Invalid response format!", result.output)


if __name__ == "__main__":
    unittest.main()
