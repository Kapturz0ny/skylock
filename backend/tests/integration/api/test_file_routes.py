from io import BytesIO
import pytest
from skylock.utils.path import UserPath


@pytest.fixture(autouse=True)
def preconfigured_files(skylock, mock_user):
    user_path_folder = UserPath(path="folder1", owner=mock_user)
    user_path_file1 = UserPath(path="file1.txt", owner=mock_user)
    user_path_file2 = UserPath(path="folder1/file2.txt", owner=mock_user)
    skylock.create_folder(user_path_folder)
    skylock.upload_file(user_path=user_path_file1, file_data=b"File 1 content", size=10)
    skylock.upload_file(user_path=user_path_file2, file_data=b"File 2 content", size=20)


# GET methods
def test_download_file_success(client):
    response = client.get("/download/files/file1.txt")
    assert response.status_code == 200
    assert response.content == b"File 1 content"


def test_download_file_not_found(client):
    response = client.get("/download/files/missing_file.txt")
    assert response.status_code == 404


def test_download_file_empty_path(client):
    response = client.get("/download/files/")
    assert response.status_code == 400


# POST methods
def test_upload_file_success(client, mock_user, skylock):
    file_data = {"file": ("file3.txt", b"File 1 content")}
    response = client.post("/files/upload/file3.txt", files=file_data)
    assert response.status_code == 201
    assert (
        skylock.download_file(UserPath(path="file3.txt", owner=mock_user)).data.read()
        == b"File 1 content"
    )


def test_upload_file_already_exists(client):
    file_data = {"file": ("file1.txt", b"New content")}
    response = client.post("/files/upload/file1.txt", files=file_data)
    assert response.status_code == 409


def test_upload_file_empty_path(client):
    file_data = {"file": ("", b"Content")}
    response = client.post("/files/upload/", files=file_data)
    assert response.status_code == 400


# DELETE methods
def test_delete_file_success(client):
    response = client.delete("/files/file1.txt")
    assert response.status_code == 204


def test_delete_file_not_found(client):
    response = client.delete("/files/missing_file.txt")
    assert response.status_code == 404
