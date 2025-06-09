"""
Module to test the nav module
"""

import unittest
from unittest.mock import patch
from http import HTTPStatus
from io import StringIO
from pathlib import Path
from click import exceptions
from skylock_cli.core.nav import list_directory, change_directory
from skylock_cli.model.file import File
from skylock_cli.model.directory import Directory
from skylock_cli.model.privacy import Privacy
from tests.helpers import mock_response_with_status



class TestListDirectory(unittest.TestCase):
    """Test the list_directory function"""

    @patch("skylock_cli.api.nav_requests.client.get")
    def test_list_directory_user_unathorized(self, mock_get):
        """Test successful directory listing"""
        mock_get.return_value = mock_response_with_status(HTTPStatus.UNAUTHORIZED)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                list_directory("/test")
            self.assertIn(
                "User is unauthorized. Please login to use this command.",
                mock_stderr.getvalue(),
            )

    @patch("skylock_cli.core.nav.send_ls_request")
    def test_list_directory_success(self, mock_send_ls_request):
        """Test successful directory listing"""
        mock_files = [
            {"name": "file1.txt", "path": "/test/file1.txt", "privacy": Privacy.PRIVATE, "size": 10},
            {"name": "file2.txt", "path": "/test/file2.txt", "privacy": Privacy.PUBLIC, "size": 20},
        ]
        mock_folders = [
            {"name": "folder1", "path": "/test/folder1", "privacy": Privacy.PRIVATE},
            {"name": "folder2", "path": "/test/folder2", "privacy": Privacy.PUBLIC},
        ]

        mock_send_ls_request.return_value = {
            "files": mock_files,
            "folders": mock_folders,
            "links": []
        }

        result, path = list_directory("/test")

        expected_result = [
            File(
                name="file1.txt",
                size=10,
                path="/test/file1.txt",
                privacy=Privacy.PRIVATE,
                type_label="file",
            ),
            File(
                name="file2.txt",
                size=20,
                path="/test/file2.txt",
                privacy=Privacy.PUBLIC,
                type_label="file",
            ),
            Directory(
                name="folder1/",
                path="/test/folder1/",
                privacy=Privacy.PRIVATE,
                type_label="directory",
            ),
            Directory(
                name="folder2/",
                path="/test/folder2/",
                privacy=Privacy.PUBLIC,
                type_label="directory",
            ),
        ]

        self.assertEqual(result, expected_result)
        self.assertEqual(path, Path("/test"))

    @patch("skylock_cli.api.nav_requests.client.get")
    def test_change_directory_user_unathorized(self, mock_get):
        """Test successful directory change"""
        mock_get.return_value = mock_response_with_status(HTTPStatus.UNAUTHORIZED)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                change_directory("/test")
            self.assertIn(
                "User is unauthorized. Please login to use this command.",
                mock_stderr.getvalue(),
            )

    @patch("skylock_cli.core.nav.send_ls_request")
    def test_list_directory_success_only_files(self, mock_send_ls_request):
        """Test successful directory listing"""
        mock_files = [
            {"name": "file1.txt", "path": "/test/file1.txt", "size": 10, "privacy": Privacy.PUBLIC},
            {"name": "file2.txt", "path": "/test/file2.txt", "size": 20, "privacy": Privacy.PRIVATE},
        ]
        mock_folders = []

        mock_send_ls_request.return_value = {
            "files": mock_files,
            "folders": mock_folders,
            "links": []
        }

        result, path = list_directory("/test")

        expected_result = [
            File(name="file1.txt", path="/test/file1.txt", size=10, privacy = Privacy.PUBLIC),
            File(name="file2.txt", path="/test/file2.txt", size=20, privacy = Privacy.PRIVATE),
        ]

        self.assertEqual(result, expected_result)
        self.assertEqual(path, Path("/test"))

    @patch("skylock_cli.core.nav.send_ls_request")
    def test_list_directory_success_only_folders(self, mock_send_ls_request):
        """Test successful directory listing"""
        mock_files = []
        mock_folders = [
            {"name": "folder1", "path": "/test/folder1"},
            {"name": "folder2", "path": "/test/folder2"},
        ]

        mock_send_ls_request.return_value = {
            "files": mock_files,
            "folders": mock_folders,
            "links": []
        }

        result, path = list_directory("/test")

        expected_result = [
            Directory(name="folder1/", path="/test/folder1/"),
            Directory(name="folder2/", path="/test/folder2/"),
        ]

        self.assertEqual(result, expected_result)
        self.assertEqual(path, Path("/test"))

    @patch("skylock_cli.core.nav.send_ls_request")
    def test_list_directory_success_empty_response(self, mock_send_ls_request):
        """Test successful directory listing"""
        mock_send_ls_request.return_value = {"files": [], "folders": [], "links": []}

        result, path = list_directory("/test")

        self.assertEqual(result, [])
        self.assertEqual(path, Path("/test"))

    @patch("skylock_cli.api.nav_requests.client.get")
    def test_list_directory_not_found(self, mock_get):
        """Test successful directory listing"""
        mock_get.return_value = mock_response_with_status(HTTPStatus.NOT_FOUND)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                list_directory("/test")
            self.assertIn(
                "Directory `/test` does not exist!",
                mock_stderr.getvalue(),
            )

    @patch("skylock_cli.api.nav_requests.client.get")
    def test_list_directory_invalid_response_format(self, mock_get):
        """Test successful directory listing"""
        mock_get.return_value = mock_response_with_status(
            HTTPStatus.OK, {"folders": []}
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                list_directory("/test")
            self.assertIn(
                "Invalid response format!",
                mock_stderr.getvalue(),
            )

    @patch("skylock_cli.api.nav_requests.client.get")
    def test_list_directory_internal_server_error(self, mock_get):
        """Test successful directory listing"""
        mock_get.return_value = mock_response_with_status(
            HTTPStatus.INTERNAL_SERVER_ERROR
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                list_directory("/test")
            self.assertIn(
                "Failed to list directory (Error Code: 500)",
                mock_stderr.getvalue(),
            )


class TestChangeDirectory(unittest.TestCase):
    """Test the change_directory function"""

    @patch("skylock_cli.core.nav.send_cd_request")
    def test_change_directory_success(self, mock_send_cd_request):
        """Test successful directory change"""
        mock_send_cd_request.return_value = None

        with patch(
            "skylock_cli.core.nav.context_manager.ContextManager.save_context"
        ) as mock_save_context:
            result = change_directory("/test")

            self.assertEqual(result, Path("/test"))
            mock_save_context.assert_called_once()

    @patch("skylock_cli.api.nav_requests.client.get")
    def test_change_directory_not_found(self, mock_get):
        """Test successful directory change"""
        mock_get.return_value = mock_response_with_status(HTTPStatus.NOT_FOUND)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                change_directory("/test")
            self.assertIn(
                "Directory `/test` does not exist!",
                mock_stderr.getvalue(),
            )

    @patch("skylock_cli.api.nav_requests.client.get")
    def test_change_directory_internal_server_error(self, mock_get):
        """Test successful directory change"""
        mock_get.return_value = mock_response_with_status(
            HTTPStatus.INTERNAL_SERVER_ERROR
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                change_directory("/test")
            self.assertIn(
                "Failed to change directory (Error Code: 500)",
                mock_stderr.getvalue(),
            )


if __name__ == "__main__":
    unittest.main()
