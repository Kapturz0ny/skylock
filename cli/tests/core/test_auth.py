"""
Test cases for the functions from core.auth
"""

import unittest
from unittest.mock import patch, Mock
from io import StringIO
from http import HTTPStatus
from click import exceptions
from httpx import ConnectError
from skylock_cli.core.auth import register_user, login_user
from skylock_cli.model.context import Context
from skylock_cli.model.token import Token
from tests.helpers import mock_response_with_status


class TestRegisterUser(unittest.TestCase):
    """Test cases for the register_user function from core.auth"""

    @patch("skylock_cli.api.auth_requests.client.post")
    def test_register_success(self, mock_post):
        """Test successful registration"""
        mock_post.return_value = mock_response_with_status(HTTPStatus.CREATED)

        register_user("testuser", "testpass", "k@g.com")
        mock_post.assert_called_once()

    @patch("skylock_cli.api.auth_requests.client.post")
    def test_register_user_already_exists(self, mock_post):
        """Test registration when the user already exists"""
        mock_post.return_value = mock_response_with_status(HTTPStatus.CONFLICT)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                register_user("testuser", "testpass")
            self.assertIn(
                "User with username `testuser` already exists!", mock_stderr.getvalue()
            )

    @patch("skylock_cli.api.auth_requests.client.post")
    def test_register_skylock_api_error(self, mock_post):
        """Test registration with a SkyLockAPIError"""
        mock_post.return_value = mock_response_with_status(
            HTTPStatus.INTERNAL_SERVER_ERROR
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                register_user("testuser", "testpass")
            self.assertIn("Failed to register user", mock_stderr.getvalue())

    @patch("skylock_cli.api.auth_requests.client.post")
    def test_register_connection_error(self, mock_post):
        """Test registration when a ConnectError occurs (backend is offline)"""
        mock_post.side_effect = ConnectError("Failed to connect to the server")

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                register_user("testuser", "testpass")
            self.assertIn(
                "The server is not reachable at the moment. Please try again later.",
                mock_stderr.getvalue(),
            )


class TestLoginUser(unittest.TestCase):
    """Test cases for the login_user function from core.auth"""

    @patch("skylock_cli.api.auth_requests.client.post")
    @patch("skylock_cli.core.auth.ContextManager.save_context")
    def test_login_success(self, mock_save_context, mock_post):
        """Test successful login"""
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.json.return_value = {
            "access_token": "test_token",
            "token_type": "bearer",
        }
        mock_post.return_value = mock_response

        login_user("testuser", "testpass")
        mock_post.assert_called_once()
        mock_save_context.assert_called_once()

        args, _ = mock_save_context.call_args
        context = args[0]
        self.assertIsInstance(context, Context)
        self.assertIsInstance(context.token, Token)
        self.assertEqual(context.token.access_token, "test_token")
        self.assertEqual(context.token.token_type, "bearer")

    @patch("skylock_cli.api.auth_requests.client.post")
    def test_login_token_not_found(self, mock_post):
        """Test login when the token is not found in the response"""
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                login_user("testuser", "testpass")
            self.assertIn("Token not found in the response", mock_stderr.getvalue())

    @patch("skylock_cli.api.auth_requests.client.post")
    def test_login_authentication_error(self, mock_post):
        """Test login with authentication error"""
        mock_post.return_value = mock_response_with_status(HTTPStatus.UNAUTHORIZED)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                login_user("testuser", "wrongpass")
            self.assertIn("Invalid username or password", mock_stderr.getvalue())

    @patch("skylock_cli.api.auth_requests.client.post")
    def test_login_connection_error(self, mock_post):
        """Test login when a ConnectError occurs (backend is offline)"""
        mock_post.side_effect = ConnectError("Failed to connect to the server")

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                login_user("testuser", "testpass")
            self.assertIn(
                "The server is not reachable at the moment. Please try again later.",
                mock_stderr.getvalue(),
            )

    @patch("skylock_cli.api.auth_requests.client.post")
    def test_login_skylock_api_error(self, mock_post):
        """Test login with a SkyLockAPIError"""
        mock_post.return_value = mock_response_with_status(
            HTTPStatus.INTERNAL_SERVER_ERROR
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                login_user("testuser", "testpass")
            self.assertIn("Failed to login user", mock_stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
