from unittest.mock import MagicMock, patch, ANY

import argon2
import pytest
import uuid

from skylock.utils.exceptions import (
    InvalidCredentialsException,
    UserAlreadyExists,
    Wrong2FAException,
)
from skylock.database.models import UserEntity
from skylock.database.repository import UserRepository
from skylock.api.models import Token

from skylock.service.user_service import UserService


@pytest.fixture
def mock_user_repository():
    return MagicMock(spec=UserRepository)


@pytest.fixture
def user_service(mock_user_repository):
    return UserService(user_repository=mock_user_repository, redis_mem=MagicMock())


@pytest.fixture
def user_data():
    return {
        "id": str(uuid.uuid4()),
        "username": "testuser",
        "password": "password123",
        "hashed_password": argon2.PasswordHasher().hash("password123"),
        "email": "test@example.com",
    }


@pytest.fixture
def user_entity(user_data):
    return UserEntity(
        id=user_data["id"],
        username=user_data["username"],
        password=user_data["hashed_password"],
        email=user_data["email"],
    )


@patch("skylock.service.user_service.send_mail")
def test_register_user_successful(send_mail, user_service, mock_user_repository, user_data, user_entity):
    mock_user_repository.get_by_username.return_value = None
    mock_user_repository.get_by_email.return_value = None
    mock_user_repository.save.return_value = user_entity

    user_service.register_user(user_data["username"], user_data["email"])

    user_service.redis_mem.setex.assert_called_once_with(
        f"2fa:{user_data["username"]}", user_service.token_life + 5, ANY
    )


def test_register_user_already_exists(user_service, mock_user_repository, user_data, user_entity):
    mock_user_repository.get_by_username.return_value = user_entity
    mock_user_repository.get_by_email.return_value = user_entity

    with pytest.raises(UserAlreadyExists):
        user_service.register_user(user_data["username"], "random_email")

    with pytest.raises(UserAlreadyExists):
        user_service.register_user("random_username", user_data["email"])


def test_verify_2FA_success(mock_user_repository, user_service, user_data, user_entity):
    mock_user_repository.save.return_value = user_entity
    user_service.redis_mem.get.return_value = f"2fa:{user_data["username"]}"

    with patch("skylock.service.user_service.pyotp.TOTP.verify", return_value=True) as totp_verify:
        result = user_service.verify_2fa(
            user_data["username"],
            user_data["password"],
            "test_code",
            user_data["email"],
        )

    assert result == user_entity
    totp_verify.assert_called_once_with("test_code")


def test_verify_2FA_wrong_code(user_service, user_data):
    user_service.redis_mem.get.return_value = None

    with pytest.raises(Wrong2FAException):
        user_service.verify_2fa(
            user_data["username"],
            user_data["password"],
            "test_code",
            user_data["email"],
        )


def test_login_user_successful(user_service, mock_user_repository, user_data, user_entity):
    mock_user_repository.get_by_username.return_value = user_entity

    with patch(
        "skylock.service.user_service.create_jwt_for_user",
        return_value="fake_jwt_token",
    ) as create_jwt_for_user_mock:
        result = user_service.login_user(user_data["username"], user_data["password"])

    assert isinstance(result, Token)
    assert result.access_token == "fake_jwt_token"
    assert result.token_type == "bearer"
    create_jwt_for_user_mock.assert_called_once_with(user_entity)
    mock_user_repository.get_by_username.assert_called_once_with(user_data["username"])


def test_login_user_invalid_credentials(user_service, mock_user_repository, user_data, user_entity):
    mock_user_repository.get_by_username.return_value = user_entity

    with pytest.raises(InvalidCredentialsException):
        user_service.login_user(user_data["username"], "wrong_password")


def test_login_user_not_found(user_service, mock_user_repository, user_data):
    mock_user_repository.get_by_username.return_value = None

    with pytest.raises(InvalidCredentialsException):
        user_service.login_user(user_data["username"], user_data["password"])
