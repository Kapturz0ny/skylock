"""
Tests for the login command
"""

import unittest
import json
from pathlib import Path, PosixPath
from unittest.mock import patch
from typer.testing import CliRunner
from art import text2art
from httpx import ConnectError
from skylock_cli.model.token import Token
from skylock_cli.model.context import Context
from skylock_cli.model.directory import Directory
from skylock_cli.cli import app
from skylock_cli.exceptions import api_exceptions
from tests.helpers import assert_connect_error


class TestLoginCommand(unittest.TestCase):
    """Test cases for the login command"""

    def setUp(self):
        self.runner = CliRunner()

    @patch("skylock_cli.core.auth.send_login_request")
    @patch("skylock_cli.core.context_manager.ContextManager.ensure_context_file_exists")
    @patch(
        "skylock_cli.core.context_manager.ContextManager.context_file_path",
        Path("/tmp/test_skylock_config/test_skylock_config.json"),
    )
    def test_login_success(self, _mock_ensure_context_file_exists, mock_send):
        """Test the login command"""
        # Create a context file with old token and cwd
        config_dir_path = Path("/tmp/test_skylock_config")
        config_dir_path.mkdir(parents=True, exist_ok=True)
        config_file_path = config_dir_path / "test_skylock_config.json"

        old_token = Token(access_token="old_token", token_type="bearer")
        old_cwd = Directory(path=Path("/old_cwd"), name="old_cwd/")
        old_base_url = "https://skylock.com"
        old_context = Context(token=old_token, cwd=old_cwd, base_url=old_base_url)
        with open(config_file_path, "w", encoding="utf-8") as file:
            json.dump({"context": old_context.model_dump()}, file, indent=4)

        new_token = Token(access_token="new_token", token_type="bearer")
        mock_send.return_value = new_token

        result = self.runner.invoke(app, ["login", "testuser"], input="testpass")
        self.assertEqual(result.exit_code, 0)
        self.assertIn("User logged in successfully", result.output)
        self.assertIn("Hello, testuser", result.output)
        self.assertIn("Welcome to our file hosting service", result.output)
        self.assertIn(text2art("SkyLock"), result.output)
        self.assertIn("Your current working directory is: /", result.output)

        with open(config_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            new_context = Context(**data.get("context", {}))
            self.assertEqual(new_context.cwd.path, PosixPath("/"))
            self.assertEqual(new_context.token.access_token, "new_token")
            self.assertEqual(new_context.base_url, "https://skylock.com")

        # Clean up: delete the created file and directory
        config_file_path.unlink()
        config_dir_path.rmdir()

    @patch("skylock_cli.core.auth.send_login_request")
    def test_login_authentication_error(self, mock_send):
        """Test the login command when an AuthenticationError occurs"""
        mock_send.side_effect = api_exceptions.AuthenticationError()

        result = self.runner.invoke(app, ["login", "testuser"], input="wrongpass")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Invalid username or password", result.output)

    @patch("skylock_cli.core.auth.send_login_request")
    def test_login_skylock_api_error(self, mock_send):
        """Test the login command when a SkyLockAPIError occurs"""
        mock_send.side_effect = api_exceptions.SkyLockAPIError(
            "An unexpected API error occurred"
        )

        result = self.runner.invoke(app, ["login", "testuser"], input="testpass")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("An unexpected API error occurred", result.output)

    @patch("skylock_cli.core.auth.send_login_request")
    def test_login_token_not_found_error(self, mock_send):
        """Test the login command when a TokenNotFoundError occurs"""
        mock_send.side_effect = api_exceptions.TokenNotFoundError()

        result = self.runner.invoke(app, ["login", "testuser"], input="testpass")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Token not found in the response", result.output)

    @patch("skylock_cli.core.auth.send_login_request")
    def test_login_connection_error(self, mock_send):
        """Test the login command when a ConnectError occurs (backend is offline)"""
        mock_send.side_effect = ConnectError("Failed to connect to the server")
        result = self.runner.invoke(app, ["login", "testuser"], input="testpass")
        assert_connect_error(result)


if __name__ == "__main__":
    unittest.main()
