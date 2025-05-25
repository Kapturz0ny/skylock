import argon2

from unittest.mock import patch

from skylock.database.models import UserEntity
from skylock.utils.exceptions import Wrong2FAException


def test_register_user_success(client):
    username = "testuser"
    password = "securepassword"
    email = "test@example.com"

    with patch("skylock.skylock_facade.SkylockFacade.register_user", return_value=None):
        response = client.post(
            "/auth/register",
            json={"username": username, "password": password, "email": email},
        )
    assert response.status_code == 201



def test_register_user_already_exists(client, db_session):
    username = "existinguser"
    password = "securepassword"
    email = "test@example.com"

    existing_user = UserEntity(id=1, username=username, password=password, email=email)
    db_session.add(existing_user)
    db_session.commit()

    response = client.post(
        "/auth/register",
        json={"username": username, "password": password, "email": email},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == f"User with given username/email already exists"


@patch("skylock.skylock_facade.SkylockFacade.configure_new_user", return_value=None)
@patch("skylock.skylock_facade.SkylockFacade.verify_2fa")
def test_authenticate_user_success(verify_mock, configure_mock, client):
    username = "existinguser"
    password = "securepassword"
    email = "test@example.com"
    code = "test_code"

    user = UserEntity(id=1, username=username, password=password, email=email)
    verify_mock.return_value = user

    response = client.post(
        "/auth/2FA",
        json={"username": username, "password": password, "email": email, "code": code},
    )

    configure_mock.assert_called_once_with(user)

    verify_mock.assert_called_once_with(
        username = username,
        password = password,
        code = code,
        email = email
    )

    assert response.status_code == 201
    assert response.json()["message"] == "User successfully registered"


@patch("skylock.skylock_facade.SkylockFacade.configure_new_user", return_value=None)
@patch("skylock.skylock_facade.SkylockFacade.verify_2fa")
def test_authenticate_user_wrong_2fa(verify_mock, configure_mock, client):
    username = "existinguser"
    password = "securepassword"
    email = "test@example.com"
    code = "test_code"

    verify_mock.side_effect = Wrong2FAException

    response = client.post(
        "/auth/2FA",
        json={"username": username, "password": password, "email": email, "code": code},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Wrong 2FA code"



# def test_login_user_success(client, db_session):
#     username = "loginuser"
#     password = "securepassword"
#     email = "test@example.com"

#     existing_user = UserEntity(
#         id=1,
#         username=username,
#         password=argon2.PasswordHasher().hash(password),
#         email=email,
#     )

#     db_session.add(existing_user)
#     db_session.commit()


#     def mock_limiter(*args, **kwargs):
#         def decorator(f):
#             return f
#         return decorator

#     response = client.post("/auth/login", json={"username": username, "password": password})

#     assert response.status_code == 200
#     assert response.json()["access_token"] is not None
#     assert response.json()["token_type"] == "bearer"


# def test_login_user_invalid_credentials(client):
#     username = "invaliduser"
#     password = "wrongpassword"

#     response = client.post("/auth/login", json={"username": username, "password": password})

#     assert response.status_code == 401
#     assert response.json()["detail"] == "Invalid credentials provided"
