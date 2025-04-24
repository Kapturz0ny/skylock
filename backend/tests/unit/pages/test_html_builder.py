import pytest
from unittest.mock import MagicMock, patch

from skylock.api.models import File, Privacy
from skylock.database.models import UserEntity
from fastapi import HTTPException


def test_build_file_page_public_file(html_builder):
    file = File(
        id="file_id",
        name="file_name",
        path="file_path",
        privacy=Privacy.PUBLIC,
        shared_to=[],
        owner_id="owner_id",
    )
    download_url = "http://example.com/download"

    html_builder._skylock.get_file_for_login.return_value = file
    html_builder._url_generator.generate_download_url_for_file.return_value = (
        download_url
    )

    request = MagicMock()

    html_builder._templates.TemplateResponse = MagicMock()
    html_builder._templates.TemplateResponse.return_value = (
        request,
        "file.html",
        {"file": {"name": file.name, "path": file.path, "download_url": download_url}},
    )

    assert html_builder.build_file_page(request, "file_id") == (
        request,
        "file.html",
        {"file": {"name": file.name, "path": file.path, "download_url": download_url}},
    )


def test_build_file_page_no_token(html_builder):
    file = File(
        id="file_id",
        name="file_name",
        path="file_path",
        privacy=Privacy.PROTECTED,
        shared_to=["me"],
        owner_id="owner_id",
    )

    request = MagicMock()
    request.cookies = {}

    html_builder._skylock.get_file_for_login.return_value = file
    html_builder._url_generator.generate_download_url_for_file.return_value = (
        "http://example.com/download"
    )

    html_builder.build_login_page = MagicMock()
    html_builder.build_login_page.return_value = "login_page"

    assert html_builder.build_file_page(request, "file_id") == "login_page"


def test_build_file_page_invalid_token(html_builder):
    file = File(
        id="file_id",
        name="file_name",
        path="file_path",
        privacy=Privacy.PROTECTED,
        shared_to=["me"],
        owner_id="owner_id",
    )

    request = MagicMock()
    request.cookies = {"access_token": "Bearer invalid_token"}

    html_builder._skylock.get_file_for_login.return_value = file
    html_builder._url_generator.generate_download_url_for_file.return_value = (
        "http://example.com/download"
    )

    html_builder.build_login_page = MagicMock()
    html_builder.build_login_page.return_value = "login_page"

    with patch(
        "skylock.pages.html_builder.get_user_from_jwt",
        side_effect=HTTPException(status_code=401, detail="Invalid Token"),
    ):
        assert html_builder.build_file_page(request, "file_id") == "login_page"
        html_builder.build_login_page.assert_called_once_with(
            request, "file_id", "Invalid Token"
        )


def test_build_file_page_not_shared(html_builder):
    file = File(
        id="file_id",
        name="file_name",
        path="file_path",
        privacy=Privacy.PROTECTED,
        shared_to=[],
        owner_id="owner_id",
    )

    request = MagicMock()
    request.cookies = {"access_token": "Bearer valid_token"}

    html_builder._skylock.get_file_for_login.return_value = file
    html_builder._url_generator.generate_download_url_for_file.return_value = (
        "http://example.com/download"
    )

    html_builder.build_login_page = MagicMock()
    html_builder.build_login_page.return_value = "login_page"

    user = UserEntity(id="user_id", username="me")

    with patch(
        "skylock.pages.html_builder.get_user_from_jwt",
        return_value=user,
    ):
        assert html_builder.build_file_page(request, "file_id") == "login_page"
        html_builder.build_login_page.assert_called_once_with(
            request, "file_id", "File not shared with you"
        )
