import pytest
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from jose import jwt
from unittest.mock import Mock

from skylock.utils.security import (
    get_user_from_jwt,
    create_jwt_for_user,
    decode_jwt,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from skylock.config import JWT_SECRET
from skylock.database import models as db_models


def test_create_jwt_for_user():
    user = db_models.UserEntity(id=1, username="testuser")
    token = create_jwt_for_user(user)
    decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])

    assert decoded_token["id"] == user.id
    assert decoded_token["sub"] == user.username
    assert "exp" in decoded_token


def test_decode_jwt():
    payload = {
        "id": 1,
        "sub": "testuser",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    decoded_token = decode_jwt(token)

    assert decoded_token["id"] == payload["id"]
    assert decoded_token["sub"] == payload["sub"]
    assert decoded_token["exp"] == payload["exp"]


def test_get_user_from_jwt_valid_token():
    user = db_models.UserEntity(id=1, username="testuser")
    user_repository = Mock()
    user_repository.get_by_id.return_value = user

    token = create_jwt_for_user(user)
    retrieved_user = get_user_from_jwt(token, user_repository)

    assert retrieved_user == user


def test_get_user_from_jwt_invalid_token():
    user_repository = Mock()
    invalid_token = "invalid.token.here"

    with pytest.raises(HTTPException) as excinfo:
        get_user_from_jwt(invalid_token, user_repository)

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Invalid token"


def test_get_user_from_jwt_user_not_found():
    user_repository = Mock()
    user_repository.get_by_id.return_value = None

    user = db_models.UserEntity(id=1, username="testuser")
    token = create_jwt_for_user(user)

    with pytest.raises(HTTPException) as excinfo:
        get_user_from_jwt(token, user_repository)

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Invalid token"
