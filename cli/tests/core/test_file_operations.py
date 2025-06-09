"""
Test cases for the functions from core.file_operations
"""

import tempfile
import unittest
import os
from http import HTTPStatus
from io import StringIO
from unittest.mock import patch, mock_open, Mock
from pathlib import Path
from click import exceptions
from httpx import ConnectError
from skylock_cli.core.file_operations import (
    _generate_unique_file_path,
    upload_file,
    download_file,
    remove_file,
    share_file,
    change_file_visibility
)
from tests.helpers import mock_test_context, mock_response_with_status

from skylock_cli.model.privacy import Privacy


class TestGenerateUniqueFilePath(unittest.TestCase):
    """
    Test cases for the _generate_unique_file_path function
    """

    @patch("skylock_cli.core.file_operations.tempfile.NamedTemporaryFile")
    def test_generate_unique_file_path(self, mock_tempfile):
        """
        Test the _generate_unique_file_path function
        """
        mock_tempfile.return_value.__enter__.return_value.name = "/mocked/path/file.txt"
        directory = Path("/mocked/path")
        file_name = "file.txt"

        result = _generate_unique_file_path(directory, file_name)

        self.assertEqual(result, Path("/mocked/path/file.txt"))
        mock_tempfile.assert_called_once_with(
            dir=directory, prefix="file", suffix=".txt", delete=False
        )

    @patch("skylock_cli.core.file_operations.tempfile.NamedTemporaryFile")
    def test_generate_unique_file_path_with_different_extension(self, mock_tempfile):
        """
        Test the _generate_unique_file_path function with a different file extension
        """
        mock_tempfile.return_value.__enter__.return_value.name = "/mocked/path/file.pdf"
        directory = Path("/mocked/path")
        file_name = "file.pdf"

        result = _generate_unique_file_path(directory, file_name)

        self.assertEqual(result, Path("/mocked/path/file.pdf"))
        mock_tempfile.assert_called_once_with(
            dir=directory, prefix="file", suffix=".pdf", delete=False
        )

    @patch("skylock_cli.core.file_operations.tempfile.NamedTemporaryFile")
    def test_generate_unique_file_path_with_no_extension(self, mock_tempfile):
        """
        Test the _generate_unique_file_path function with no file extension
        """
        mock_tempfile.return_value.__enter__.return_value.name = "/mocked/path/file"
        directory = Path("/mocked/path")
        file_name = "file"

        result = _generate_unique_file_path(directory, file_name)

        self.assertEqual(result, Path("/mocked/path/file"))
        mock_tempfile.assert_called_once_with(
            dir=directory, prefix="file", suffix="", delete=False
        )


class TestUploadFile(unittest.TestCase):
    """
    Test cases for the upload_file function
    """

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.core.file_operations.file_requests.send_upload_request")
    def test_upload_file_success(self, mock_send, _mock_get_context):
        """Test the upload_file function with a successful upload"""
        force_flag = False
        privacy = Privacy.PRIVATE

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = Path(temp_file.name)
            temp_file_name = temp_file_path.name
            mock_send.return_value = {
                "name": temp_file_name,
                "path": "",
                "privacy": Privacy.PRIVATE,
                "size": 10
            }
            new_file = upload_file(temp_file_path, Path("."), force_flag, privacy)

            self.assertEqual(new_file.name, temp_file_name)
            self.assertEqual(new_file.path, Path("."))
            self.assertEqual(new_file.privacy, privacy)
            self.assertEqual(new_file.size, 10)
            self.assertEqual(new_file.color, "yellow")
            self.assertEqual(new_file.type_label, "file")
            self.assertEqual(new_file.visibility_label, "private 🔐")
            self.assertEqual(new_file.visibility_color, "red")

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.core.file_operations.file_requests.send_upload_request")
    def test_upload_file_success_public(self, mock_send, _mock_get_context):
        """Test the upload_file function with a successful upload"""
        force_flag = False
        privacy = Privacy.PUBLIC

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = Path(temp_file.name)
            temp_file_name = temp_file_path.name
            mock_send.return_value = {
                "name": temp_file_name,
                "path": "",
                "size": 10,
                "privacy": Privacy.PUBLIC
            }
            new_file = upload_file(temp_file_path, Path("."), force_flag, privacy)

            self.assertEqual(new_file.name, temp_file_name)
            self.assertEqual(new_file.path, Path("."))
            self.assertEqual(new_file.privacy, Privacy.PUBLIC)
            self.assertEqual(new_file.size, 10)
            self.assertEqual(new_file.color, "yellow")
            self.assertEqual(new_file.type_label, "file")
            self.assertEqual(new_file.visibility_label, "public 🔓")
            self.assertEqual(new_file.visibility_color, "green")

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(Path("/test")),
    )
    @patch("skylock_cli.core.file_operations.file_requests.send_upload_request")
    def test_upload_file_with_different_cwd(self, mock_send, _mock_get_context):
        """Test the upload_file function with a different current working directory"""
        force_flag = False
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = Path(temp_file.name)
            temp_file_name = temp_file_path.name
            mock_send.return_value = {
                "name": temp_file_name,
                "path": "/test",
                "size": 10,
                "privacy": Privacy.PRIVATE
            }
            new_file = upload_file(temp_file_path, Path("."), force_flag)

            self.assertEqual(new_file.name, temp_file_name)
            self.assertEqual(new_file.path, Path("/test"))
            self.assertEqual(new_file.privacy, Privacy.PRIVATE),
            self.assertEqual(new_file.size, 10)
            self.assertEqual(new_file.color, "yellow")
            self.assertEqual(new_file.type_label, "file")
            self.assertEqual(new_file.visibility_label, "private 🔐")

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch(
        "skylock_cli.api.file_requests.client.post",
        return_value=mock_response_with_status(HTTPStatus.UNAUTHORIZED),
    )
    def test_upload_file_with_unauthorized_error(self, _mock_send, _mock_get_context):
        """Test the upload_file function with an unauthorized error"""
        force_flag = False
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = Path(temp_file.name)
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(exceptions.Exit):
                    upload_file(temp_file_path, Path("."), force_flag)

                self.assertIn(
                    "User is unauthorized. Please login to use this command.",
                    mock_stderr.getvalue(),
                )

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch(
        "skylock_cli.api.file_requests.client.post",
        return_value=mock_response_with_status(HTTPStatus.CONFLICT),
    )
    def test_upload_file_already_exists_no_force(self, _mock_send, _mock_get_context):
        """Test the upload_file function with an unauthorized error"""
        force_flag = False
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = Path(temp_file.name)
            temp_file_name = os.path.basename(temp_file_path)
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(exceptions.Exit):
                    upload_file(temp_file_path, Path("."), force_flag)

                self.assertIn(
                    f"File `/{temp_file_name}` already exists! Use the --force flag to overwrite it.",
                    mock_stderr.getvalue(),
                )

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch(
        "skylock_cli.api.file_requests.client.post",
        return_value=mock_response_with_status(HTTPStatus.CONFLICT),
    )
    def test_upload_file_already_exists_force(self, _mock_send, _mock_get_context):
        """Test the upload_file function with an unauthorized error"""
        force_flag = True
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = Path(temp_file.name)
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(exceptions.Exit):
                    upload_file(temp_file_path, Path("."), force_flag)

                self.assertIn(
                    "Failed to upload file (Error Code: 409)",
                    mock_stderr.getvalue(),
                )

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch(
        "skylock_cli.api.file_requests.client.post",
        return_value=mock_response_with_status(HTTPStatus.BAD_REQUEST),
    )
    def test_upload_file_dest_path_does_not_exists(self, _mock_send, _mock_get_context):
        """Test the upload_file function with an unauthorized error"""
        force_flag = False
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = Path(temp_file.name)
            temp_file_name = os.path.basename(temp_file_path)
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(exceptions.Exit):
                    upload_file(temp_file_path, Path("."), force_flag)

                self.assertIn(
                    f"Invalid path `/{temp_file_name}`!", mock_stderr.getvalue()
                )

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch(
        "skylock_cli.api.file_requests.client.post",
        return_value=mock_response_with_status(HTTPStatus.INTERNAL_SERVER_ERROR),
    )
    def test_upload_file_with_internal_server_error(
        self, _mock_send, _mock_get_context
    ):
        """Test the upload_file function with an unauthorized error"""
        force_flag = False
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = Path(temp_file.name)
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(exceptions.Exit):
                    upload_file(temp_file_path, Path("."), force_flag)

                self.assertIn(
                    "Failed to upload file (Error Code: 500)", mock_stderr.getvalue()
                )

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch(
        "skylock_cli.api.file_requests.client.post",
        return_value=mock_response_with_status(HTTPStatus.NOT_FOUND),
    )
    def test_upload_file_when_destination_directory_does_not_exist(
        self, _mock_send, _mock_get_context
    ):
        """Test the upload_file function with a not found error"""
        force_flag = False
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = Path(temp_file.name)
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(exceptions.Exit):
                    upload_file(temp_file_path, Path("."), force_flag)

                self.assertIn("Directory `/` does not exist!", mock_stderr.getvalue())

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.api.file_requests.client.post")
    def test_upload_file_with_connection_error(self, mock_send, _mock_get_context):
        """Test the upload_file function with a connection error"""
        mock_send.side_effect = ConnectError("Failed to connect to the server")
        force_flag = False
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = Path(temp_file.name)
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(exceptions.Exit):
                    upload_file(temp_file_path, Path("."), force_flag)

                self.assertIn(
                    "The server is not reachable at the moment. Please try again later.",
                    mock_stderr.getvalue(),
                )


class TestDownloadFile(unittest.TestCase):
    """
    Test cases for the download_file function
    """

    @patch("skylock_cli.core.file_operations.create_downloads_dir", return_value=None)
    @patch(
        "skylock_cli.core.file_operations._generate_unique_file_path",
        return_value=Path("/mocked/Downloads/file.txt"),
    )
    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch(
        "skylock_cli.core.file_operations.file_requests.send_download_request",
        return_value=b"123\nabc",
    )
    @patch("skylock_cli.core.file_operations.Path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_download_file_target_path_exists(
        self,
        _mock_open,
        _mock_exists,
        _mock_send,
        _mock_get_context,
        _mock_generate_unique,
        _mock_create_downloads_dir,
    ):
        """Test the download_file function with a successful download"""
        result = download_file(Path("file.txt"))
        self.assertEqual(result, Path("/mocked/Downloads/file.txt"))
        _mock_open.assert_called_once_with(Path("/mocked/Downloads/file.txt"), "wb")
        _mock_open().write.assert_called_once_with(b"123\nabc")

    @patch(
        "skylock_cli.core.file_operations.DOWNLOADS_DIR", new=Path("/mocked/Downloads/")
    )
    @patch("skylock_cli.core.file_operations.create_downloads_dir", return_value=None)
    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch(
        "skylock_cli.core.file_operations.file_requests.send_download_request",
        return_value=b"123\nabc",
    )
    @patch("skylock_cli.core.file_operations.Path.exists", return_value=False)
    @patch("builtins.open", new_callable=mock_open)
    def test_download_file_target_path_does_not_exist(
        self,
        _mock_open,
        _mock_exists,
        _mock_send,
        _mock_get_context,
        _mock_create_downloads_dir,
    ):
        """Test the download_file function when target_file_path does not exists"""
        result = download_file(Path("file.txt"))
        self.assertEqual(result, Path("/mocked/Downloads/file.txt"))
        self.assertEqual(result.parent, Path("/mocked/Downloads"))
        _mock_open.assert_called_once_with(Path("/mocked/Downloads/file.txt"), "wb")
        _mock_open().write.assert_called_once_with(b"123\nabc")

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch(
        "skylock_cli.api.file_requests.client.get",
        return_value=mock_response_with_status(HTTPStatus.UNAUTHORIZED),
    )
    def test_download_file_with_unauthorized_error(self, _mock_send, _mock_get_context):
        """Test the download_file function with an unauthorized error"""
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                download_file(Path("file.txt"))

            self.assertIn(
                "User is unauthorized. Please login to use this command.",
                mock_stderr.getvalue(),
            )

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch(
        "skylock_cli.api.file_requests.client.get",
        return_value=mock_response_with_status(HTTPStatus.BAD_REQUEST),
    )
    def test_download_file_with_invalid_path_error(self, _mock_send, _mock_get_context):
        """Test the download_file function with an invalid path error"""
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                download_file(Path("/$/file.txt"))

            self.assertIn(
                "Invalid path `/$/file.txt`!",
                mock_stderr.getvalue(),
            )

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(Path("/test")),
    )
    @patch(
        "skylock_cli.api.file_requests.client.get",
        return_value=mock_response_with_status(HTTPStatus.NOT_FOUND),
    )
    def test_download_file_with_not_found_error(self, _mock_send, _mock_get_context):
        """Test the download_file function with a not found error"""
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                download_file(Path("non_existent_file.txt"))

            self.assertIn(
                "File `/test/non_existent_file.txt` does not exist!",
                mock_stderr.getvalue(),
            )

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.api.file_requests.client.get")
    def test_download_file_with_invalid_response_format_error(
        self, mock_send, _mock_get_context
    ):
        """Test the download_file function with an invalid response format error"""
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.content = None
        mock_send.return_value = mock_response

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                download_file(Path("file.txt"))

            self.assertIn(
                "Invalid response format!",
                mock_stderr.getvalue(),
            )

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.api.file_requests.client.get")
    def test_download_file_with_connection_error(self, mock_send, _mock_get_context):
        """Test the download function with a connection error"""
        mock_send.side_effect = ConnectError("Failed to connect to the server")
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                download_file(Path("file.txt"))

            self.assertIn(
                "The server is not reachable at the moment. Please try again later.",
                mock_stderr.getvalue(),
            )


class TestRemoveFile(unittest.TestCase):
    """Test cases for the remove_file function from core.file_operations"""

    @patch("skylock_cli.api.file_requests.client.delete")
    def test_remove_file_success(self, mock_delete):
        """Test successful file removal"""
        mock_delete.return_value = mock_response_with_status(HTTPStatus.NO_CONTENT)

        remove_file("test.txt")
        mock_delete.assert_called_once()

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.api.file_requests.client.delete")
    def test_remove_file_not_found(self, mock_delete, _mock_get_context):
        """Test removal when the file is not found"""
        mock_delete.return_value = mock_response_with_status(HTTPStatus.NOT_FOUND)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                remove_file("test.txt")
            self.assertIn("File `/test.txt` does not exist!", mock_stderr.getvalue())

    @patch("skylock_cli.api.file_requests.client.delete")
    def test_remove_file_skylock_api_error(self, mock_delete):
        """Test removal with a SkyLockAPIError"""
        mock_delete.return_value = mock_response_with_status(
            HTTPStatus.INTERNAL_SERVER_ERROR
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                remove_file("test.txt")
            self.assertIn(
                "Failed to remove file (Error Code: 500)",
                mock_stderr.getvalue(),
            )

    @patch("skylock_cli.api.file_requests.client.delete")
    def test_remove_file_connection_error(self, mock_delete):
        """Test removal when a ConnectError occurs (backend is offline)"""
        mock_delete.side_effect = ConnectError("Failed to connect to the server")
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                remove_file("test.txt")
            self.assertIn(
                "The server is not reachable at the moment. Please try again later.",
                mock_stderr.getvalue(),
            )

    def test_remove_not_a_file_error(self):
        """Test removal when the path is not a file"""

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                remove_file("test_dir/")
            self.assertIn("test_dir/ is not a file", mock_stderr.getvalue())

    @patch("skylock_cli.api.file_requests.client.delete")
    def test_remove_file_unauthorized(self, mock_delete):
        """Test removal when the user is unauthorized"""
        mock_delete.return_value = mock_response_with_status(HTTPStatus.UNAUTHORIZED)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                remove_file("test.txt")
            self.assertIn(
                "User is unauthorized. Please login to use this command.",
                mock_stderr.getvalue(),
            )


class TestMakeFilePublic(unittest.TestCase):
    """Test cases for the change_file_visibility function with param privacy=Privacy.PUBLIC from core.file_operations"""

    @patch("skylock_cli.api.file_requests.client.patch")
    def test_make_file_public_success(self, mock_patch):
        """Test successful file public access"""
        response_json = {"name": "test.txt", "path": "", "size": 10, "privacy": Privacy.PUBLIC}
        mock_patch.return_value = mock_response_with_status(
            HTTPStatus.OK, response_json
        )

        changed_file = change_file_visibility("test.txt", Privacy.PUBLIC, [])
        mock_patch.assert_called_once()
        self.assertEqual(changed_file.name, "test.txt")
        self.assertEqual(changed_file.path, Path("."))
        self.assertEqual(changed_file.privacy, Privacy.PUBLIC)
        self.assertEqual(changed_file.color, "yellow")
        self.assertEqual(changed_file.type_label, "file")
        self.assertEqual(changed_file.visibility_label, "public 🔓")

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.api.file_requests.client.patch")
    def test_make_file_public_not_found(self, mock_patch, _mock_get_context):
        """Test making a file public when the file is not found"""
        mock_patch.return_value = mock_response_with_status(HTTPStatus.NOT_FOUND)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                change_file_visibility("test.txt", Privacy.PUBLIC, [])
            self.assertIn("File `/test.txt` does not exist!", mock_stderr.getvalue())

    @patch("skylock_cli.api.file_requests.client.patch")
    def test_make_file_public_skylock_api_error(self, mock_patch):
        """Test making a file public with a SkyLockAPIError"""
        mock_patch.return_value = mock_response_with_status(
            HTTPStatus.INTERNAL_SERVER_ERROR
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                change_file_visibility("test.txt", Privacy.PUBLIC, [])
            self.assertIn(
                "Failed to make file public (Error Code: 500)",
                mock_stderr.getvalue(),
            )

    @patch("skylock_cli.api.file_requests.client.patch")
    def test_make_file_public_connection_error(self, mock_patch):
        """Test making a file public when a ConnectError occurs (backend is offline)"""
        mock_patch.side_effect = ConnectError("Failed to connect to the server")
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                change_file_visibility("test.txt", Privacy.PUBLIC, [])
            self.assertIn(
                "The server is not reachable at the moment. Please try again later.",
                mock_stderr.getvalue(),
            )


class TestMakeFilePrivate(unittest.TestCase):
    """Test cases for the change_file_visibility function with param privacy=Privacy.PRIVATE from core.file_operations"""

    @patch("skylock_cli.api.file_requests.client.patch")
    def test_make_file_private_success(self, mock_patch):
        """Test successful file private access"""
        response_json = {"name": "test.txt", "path": "", "size": 10, "privacy": Privacy.PRIVATE}
        mock_patch.return_value = mock_response_with_status(
            HTTPStatus.OK, response_json
        )

        changed_file = change_file_visibility("test.txt", Privacy.PRIVATE, [])
        mock_patch.assert_called_once()
        self.assertEqual(changed_file.name, "test.txt")
        self.assertEqual(changed_file.path, Path("."))
        self.assertEqual(changed_file.privacy, Privacy.PRIVATE)
        self.assertEqual(changed_file.color, "yellow")
        self.assertEqual(changed_file.type_label, "file")
        self.assertEqual(changed_file.visibility_label, "private 🔐")

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.api.file_requests.client.patch")
    def test_make_file_private_not_found(self, mock_patch, _mock_get_context):
        """Test making a file private when the file is not found"""
        mock_patch.return_value = mock_response_with_status(HTTPStatus.NOT_FOUND)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                change_file_visibility("test.txt", Privacy.PRIVATE, [])
            self.assertIn("File `/test.txt` does not exist!", mock_stderr.getvalue())

    @patch("skylock_cli.api.file_requests.client.patch")
    def test_make_file_private_connection_error(self, mock_patch):
        """Test making a file private when a ConnectError occurs (backend is offline)"""
        mock_patch.side_effect = ConnectError("Failed to connect to the server")
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                change_file_visibility("test.txt", Privacy.PRIVATE, [])
            self.assertIn(
                "The server is not reachable at the moment. Please try again later.",
                mock_stderr.getvalue(),
            )

    @patch("skylock_cli.api.file_requests.client.patch")
    def test_make_file_private_skylock_api_error(self, mock_patch):
        """Test making a file private with a SkyLockAPIError"""
        mock_patch.return_value = mock_response_with_status(
            HTTPStatus.INTERNAL_SERVER_ERROR
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                change_file_visibility("test.txt", Privacy.PRIVATE, [])
            self.assertIn(
                "Failed to make file private (Error Code: 500)",
                mock_stderr.getvalue(),
            )


class TestMakeFileProtected(unittest.TestCase):
    """Test cases for the change_file_visibility function with param privacy=Privacy.PROTECTED from core.file_operations"""

    @patch("skylock_cli.api.file_requests.client.patch")
    def test_make_file_protected_success(self, mock_patch):
        """Test successful file private access"""
        response_json = {"name": "test.txt", "path": "", "size": 10, "privacy": Privacy.PROTECTED}
        mock_patch.return_value = mock_response_with_status(
            HTTPStatus.OK, response_json
        )

        changed_file = change_file_visibility("test.txt", Privacy.PROTECTED, [])
        mock_patch.assert_called_once()
        self.assertEqual(changed_file.name, "test.txt")
        self.assertEqual(changed_file.path, Path("."))
        self.assertEqual(changed_file.privacy, Privacy.PROTECTED)
        self.assertEqual(changed_file.color, "yellow")
        self.assertEqual(changed_file.type_label, "file")
        self.assertEqual(changed_file.visibility_label, "protected 🔐/🔒")

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.api.file_requests.client.patch")
    def test_make_file_private_not_found(self, mock_patch, _mock_get_context):
        """Test making a file private when the file is not found"""
        mock_patch.return_value = mock_response_with_status(HTTPStatus.NOT_FOUND)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                change_file_visibility("test.txt", Privacy.PRIVATE, [])
            self.assertIn("File `/test.txt` does not exist!", mock_stderr.getvalue())

    @patch("skylock_cli.api.file_requests.client.patch")
    def test_make_file_private_connection_error(self, mock_patch):
        """Test making a file private when a ConnectError occurs (backend is offline)"""
        mock_patch.side_effect = ConnectError("Failed to connect to the server")
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                change_file_visibility("test.txt", Privacy.PRIVATE, [])
            self.assertIn(
                "The server is not reachable at the moment. Please try again later.",
                mock_stderr.getvalue(),
            )

    @patch("skylock_cli.api.file_requests.client.patch")
    def test_make_file_private_skylock_api_error(self, mock_patch):
        """Test making a file private with a SkyLockAPIError"""
        mock_patch.return_value = mock_response_with_status(
            HTTPStatus.INTERNAL_SERVER_ERROR
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                change_file_visibility("test.txt", Privacy.PRIVATE, [])
            self.assertIn(
                "Failed to make file private (Error Code: 500)",
                mock_stderr.getvalue(),
            )



class TestShareFile(unittest.TestCase):
    """Test cases for the share_file function from core.file_operations"""

    @patch("skylock_cli.api.file_requests.client.get")
    def test_share_file_empty_location_in_body(self, mock_get):
        """Test sharing when the response body has an unexpected format"""
        mock_get.return_value = mock_response_with_status(
            HTTPStatus.OK, json_data={"location": ""}
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                share_file("test.txt")
            self.assertIn(
                "Invalid response format!",
                mock_stderr.getvalue(),
            )

    @patch("skylock_cli.core.context_manager.ContextManager.get_context")
    @patch("skylock_cli.api.file_requests.client.get")
    def test_share_file_success(self, mock_get, mock_context):
        """Test successful file sharing"""
        response_json = {"location": "/files/349248263498632"}
        mock_get.return_value = mock_response_with_status(HTTPStatus.OK, response_json)
        mock_context.return_value = mock_test_context()

        shared_link = share_file("test.txt")
        mock_get.assert_called_once()
        self.assertEqual(shared_link.location, "/files/349248263498632")
        self.assertEqual(shared_link.base_url, "http://localhost:8000")
        self.assertEqual(shared_link.url, "http://localhost:8000/files/349248263498632")

    @patch("skylock_cli.api.file_requests.client.get")
    def test_share_file_no_location_in_body(self, mock_get):
        """Test sharing when the response body has an unexpected format"""
        mock_get.return_value = mock_response_with_status(
            HTTPStatus.OK, json_data={"token": "123618246812548152"}
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                share_file("test.txt")
            self.assertIn(
                "Invalid response format!",
                mock_stderr.getvalue(),
            )

    @patch("skylock_cli.core.context_manager.ContextManager.get_context")
    @patch("skylock_cli.api.file_requests.client.get")
    def test_share_file_success_different_base_url(self, mock_get, mock_context):
        """Test successful directory sharing with a different base URL"""
        response_json = {"location": "/files/349248263498632"}
        mock_get.return_value = mock_response_with_status(HTTPStatus.OK, response_json)
        mock_context.return_value = mock_test_context(base_url="http://skylock.com")

        share_link = share_file("test.txt")
        mock_get.assert_called_once()
        self.assertEqual(share_link.base_url, "http://skylock.com")
        self.assertEqual(share_link.location, "/files/349248263498632")
        self.assertEqual(share_link.url, "http://skylock.com/files/349248263498632")

    @patch("skylock_cli.api.file_requests.client.get")
    def test_share_file_connection_error(self, mock_get):
        """Test sharing a file when a ConnectError occurs (backend is offline)"""
        mock_get.side_effect = ConnectError("Failed to connect to the server")
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                share_file("test.txt")
            self.assertIn(
                "The server is not reachable at the moment. Please try again later.",
                mock_stderr.getvalue(),
            )

    @patch("skylock_cli.core.context_manager.ContextManager.get_context")
    @patch("skylock_cli.api.file_requests.client.get")
    def test_share_file_unathorized(self, mock_get, mock_context):
        """Test sharing a file when the user is unauthorized"""
        mock_get.return_value = mock_response_with_status(HTTPStatus.UNAUTHORIZED)
        mock_context.return_value = mock_test_context()

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                share_file("test.txt")
            self.assertIn(
                "User is unauthorized. Please login to use this command.",
                mock_stderr.getvalue(),
            )

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.api.file_requests.client.get")
    def test_share_file_not_found(self, mock_get, _mock_get_context):
        """Test sharing a file when the file is not found"""
        mock_get.return_value = mock_response_with_status(HTTPStatus.NOT_FOUND)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                share_file("test.txt")
            self.assertIn("File `/test.txt` does not exist!", mock_stderr.getvalue())

    @patch(
        "skylock_cli.core.context_manager.ContextManager.get_context",
        return_value=mock_test_context(),
    )
    @patch("skylock_cli.api.file_requests.client.get")
    def test_share_file_not_public(self, mock_get, _mock_get_context):
        """Test sharing a file that is not public"""
        mock_get.return_value = mock_response_with_status(HTTPStatus.FORBIDDEN)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                share_file("test.txt")
            self.assertIn(
                "File `/test.txt` is not public!",
                mock_stderr.getvalue(),
            )

    @patch("skylock_cli.api.file_requests.client.get")
    def test_share_file_invalid_response_format(self, mock_get):
        """Test sharing a file with an invalid response format"""
        mock_get.return_value = mock_response_with_status(HTTPStatus.OK, json_data={})

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                share_file("test.txt")
            self.assertIn("Invalid response format!", mock_stderr.getvalue())

    @patch("skylock_cli.api.file_requests.client.get")
    def test_share_file_skylock_api_error(self, mock_get):
        """Test sharing with a SkyLockAPIError"""
        mock_get.return_value = mock_response_with_status(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            json_data={"location": "/folders/11222333"},
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with self.assertRaises(exceptions.Exit):
                share_file("test.txt")
            self.assertIn(
                "Failed to share file (Error Code: 500)",
                mock_stderr.getvalue(),
            )


if __name__ == "__main__":
    unittest.main()
