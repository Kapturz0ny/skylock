"""
Tests for the share command
"""

import unittest
from unittest.mock import patch
from typer.testing import CliRunner
from httpx import ConnectError
from skylock_cli.cli import app
from skylock_cli.exceptions import api_exceptions
from tests.helpers import mock_test_context, assert_connect_error, mock_change_file_privacy

from skylock_cli.model.privacy import Privacy
from skylock_cli.model.share_link import ShareLink


class TestShareCommand(unittest.TestCase):
    """Test cases for the share command"""

    def setUp(self):
        self.runner = CliRunner()

    @patch("skylock_cli.model.token.Token.is_expired", return_value=False)
    @patch("skylock_cli.model.token.Token.is_valid", return_value=True)
    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.api.file_requests.client.patch")
    @patch("skylock_cli.cli.path_parser.is_directory")
    @patch("skylock_cli.cli.file_operations.share_file")
    def test_share_file_success(
        self,
        mock_share_file,
        mock_is_directory,
        mock_patch,
        _mock_get_context,
        _mock_is_valid,
        _mock_is_expired,
    ):
        """Test the share command on file"""
        mock_share_file.return_value = ShareLink(base_url="http://localhost:8000", location="files/349248263498632")
        mock_is_directory.return_value = False

        expected_privacy = Privacy.PRIVATE
        mock_patch.side_effect = mock_change_file_privacy(expected_privacy)

        result = self.runner.invoke(app, ["share", "file.txt"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("File /file.txt is now private", result.stdout)
        self.assertIn("Current working directory: /", result.stdout)
        self.assertIn(
            "URL to shared resource: http://localhost:8000/files/349248263498632",
            result.stdout,
        )

    @patch("skylock_cli.model.token.Token.is_expired", return_value=False)
    @patch("skylock_cli.model.token.Token.is_valid", return_value=True)
    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.api.file_requests.client.patch")
    @patch("skylock_cli.cli.path_parser.is_directory")
    @patch("skylock_cli.cli.file_operations.share_file")
    def test_share_file_success_public(
        self,
        mock_share_file,
        mock_is_directory,
        mock_patch,
        _mock_get_context,
        _mock_is_valid,
        _mock_is_expired,
    ):
        """Test the share command on file"""
        mock_share_file.return_value = ShareLink(base_url="http://localhost:8000", location="files/349248263498632")
        mock_is_directory.return_value = False

        expected_privacy = Privacy.PUBLIC
        mock_patch.side_effect = mock_change_file_privacy(expected_privacy)

        result = self.runner.invoke(app, ["share", "file.txt", "--mode", "public"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("File /file.txt is now public", result.stdout)
        self.assertIn("Current working directory: /", result.stdout)
        self.assertIn(
            "URL to shared resource: http://localhost:8000/files/349248263498632",
            result.stdout,
        )

    @patch("skylock_cli.model.token.Token.is_expired", return_value=False)
    @patch("skylock_cli.model.token.Token.is_valid", return_value=True)
    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.api.file_requests.client.patch")
    @patch("skylock_cli.cli.path_parser.is_directory")
    @patch("skylock_cli.cli.file_operations.share_file")
    def test_share_file_success_protected(
        self,
        mock_share_file,
        mock_is_directory,
        mock_patch,
        _mock_get_context,
        _mock_is_valid,
        _mock_is_expired,
    ):
        """Test the share command on file"""
        mock_share_file.return_value = ShareLink(base_url="http://localhost:8000", location="files/349248263498632")
        mock_is_directory.return_value = False

        expected_privacy = Privacy.PROTECTED
        mock_patch.side_effect = mock_change_file_privacy(expected_privacy)

        result = self.runner.invoke(app, ["share", "file.txt", "--mode", "protected", "--to", "user"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("File /file.txt is now protected", result.stdout)
        self.assertIn("Current working directory: /", result.stdout)
        self.assertIn(
            "URL to shared resource: http://localhost:8000/files/349248263498632",
            result.stdout,
        )


    def test_share_file_protected_no_to(
        self,
    ):
        """Test the share command on file"""

        result = self.runner.invoke(app, ["share", "file.txt", "--mode", "protected"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn(
            "Error: Usernames are required for 'protected' mode.", result.output
        )

    @patch("skylock_cli.core.file_operations.file_requests.send_change_privacy")
    def test_share_file_unathorized(
        self,
        mock_send_share_request,
    ):
        """Test the share command on file with an unauthorized user"""
        mock_send_share_request.side_effect = api_exceptions.UserUnauthorizedError()

        result = self.runner.invoke(app, ["share", "file.txt"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn(
            "User is unauthorized. Please login to use this command.", result.output
        )


    @patch("skylock_cli.core.file_operations.file_requests.send_change_privacy")
    def test_share_file_not_found_error(
        self,
        mock_send_share_request,
    ):
        """Test the share command on file with a FileNotFoundError"""
        mock_send_share_request.side_effect = api_exceptions.FileNotFoundError(
            "file.txt"
        )

        result = self.runner.invoke(app, ["share", "file.txt"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("File `file.txt` does not exist!", result.output)


    @patch("skylock_cli.core.file_operations.file_requests.send_change_privacy")
    def test_share_file_wrong_reponse_format(
        self,
        mock_send_share_request,
    ):
        """Test the share command on file with a wrong response format"""
        mock_send_share_request.side_effect = (
            api_exceptions.InvalidResponseFormatError()
        )

        result = self.runner.invoke(app, ["share", "file.txt"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Invalid response format!", result.output)


    @patch("skylock_cli.core.file_operations.file_requests.send_change_privacy")
    def test_share_file_internal_server_error(
        self,
        mock_send_share_request,
    ):
        """Test the share command on file with an InternalServerError"""
        mock_send_share_request.side_effect = api_exceptions.SkyLockAPIError(
            "Failed to share file (Internal Server Error)"
        )

        result = self.runner.invoke(app, ["share", "file.txt"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Failed to share file (Internal Server Error)", result.output)


    @patch("skylock_cli.core.file_operations.file_requests.send_change_privacy")
    def test_share_file_connection_error(
        self,
        mock_send_share_request,
    ):
        """Test the share command on file with a ConnectionError"""
        mock_send_share_request.side_effect = ConnectError(
            "Failed to connect to the server"
        )
        result = self.runner.invoke(app, ["share", "file.txt"])
        assert_connect_error(result)


if __name__ == "__main__":
    unittest.main()
