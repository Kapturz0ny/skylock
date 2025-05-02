"""
Tests for the register command
"""

import unittest
import typer
from unittest.mock import patch
from typer.testing import CliRunner
from httpx import ConnectError
from skylock_cli.cli import app
from skylock_cli.exceptions import api_exceptions
from tests.helpers import assert_connect_error


class TestRegisterCommand(unittest.TestCase):
    """Test cases for the register command"""

    def setUp(self):
        self.runner = CliRunner()

    @patch("skylock_cli.core.auth.send_register_request")
    @patch("skylock_cli.core.auth.send_verify_code_request")
    def test_register_success(self, mock_send_req, mock_verify_code_req):
        mock_send_req.return_value = None
        mock_verify_code_req.return_value = None

        """Test the register command"""

        result = self.runner.invoke(
            app,
            ["register", "testuser1"],
            input="email@example.com\ntestpass1\ntestpass1\ncode",
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("User registered successfully", result.output)

    @patch("skylock_cli.core.auth.send_register_request")
    def test_register_user_already_exists(self, mock_send):
        """Test the register command when the user already exists"""
        mock_send.side_effect = api_exceptions.UserAlreadyExistsError()

        result = self.runner.invoke(
            app, ["register", "testuser"], input="email@example.com\ntestpass\ntestpass"
        )
        self.assertEqual(result.exit_code, 1)
        self.assertIn("User with given username/email already exists.", result.output)

    @patch("skylock_cli.core.auth.send_register_request")
    def test_register_skylock_api_error(self, mock_send):
        """Test the register command when a SkyLockAPIError occurs"""
        mock_send.side_effect = api_exceptions.SkyLockAPIError(
            "An unexpected API error occurred"
        )

        result = self.runner.invoke(
            app,
            ["register", "testuser2"],
            input="email@example.com\ntestpass2\ntestpass2",
        )
        self.assertEqual(result.exit_code, 1)
        self.assertIn("An unexpected API error occurred", result.output)

    def test_register_invalid_email(self):
        """Test the register command with an invalid email format"""
        result = self.runner.invoke(
            app, ["register", "testuser"], input="bad_email\ntestpass\ntestpass"
        )
        self.assertEqual(result.exit_code, 1)
        self.assertIn(
            "Invalid email address. Please enter a valid email.", result.output
        )

    @patch("skylock_cli.core.auth.send_register_request")
    def test_register_connection_error(self, mock_send):
        """Test the register command when a ConnectError occurs (backend is offline)"""
        mock_send.side_effect = ConnectError("Failed to connect to the server")
        result = self.runner.invoke(
            app,
            ["register", "testuser3"],
            input="email@example.com\ntestpass3\ntestpass3",
        )
        assert_connect_error(result)

    @patch("skylock_cli.core.auth.send_register_request")
    def test_register_password_mismatch(self, _mock_send):
        """Test the register command when the passwords do not match"""
        result = self.runner.invoke(
            app,
            ["register", "testuser4"],
            input="email@example.com\ntestpass4\ntestpass5",
        )
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Passwords do not match. Please try again.", result.output)


if __name__ == "__main__":
    unittest.main()
