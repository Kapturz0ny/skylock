from unittest.mock import MagicMock, ANY, patch
from skylock.service.user_service import UserService

@patch("skylock.service.user_service.send_mail")
def test_register_success(mock_send_mail):
    mock_user_repository = MagicMock()
    mock_user_repository.get_by_username.return_value = None
    mock_user_repository.get_by_email.return_value = None

    mock_redis = MagicMock()

    user_service = UserService(
        user_repository=mock_user_repository,
        redis_mem=mock_redis
    )

    username = "testuser"
    password = "securepassword"
    email = "testuser@example.com"

    user_service.register_user(username, password, email)

    user_service.redis_mem.setex.assert_called_once_with(
        f"2fa:{username}",
        user_service.TOKEN_LIFE + 5,
        ANY
    )

    mock_send_mail.assert_called_once_with(
        email,
        "Complete you registration to Skylock!",
        ANY
    )



def test_register_user_success(client):
    username = "testuser"
    password = "securepassword"
    email = "test@example.com"

    response = client.post("/auth/register", json={"username": username, "password": password, "email": email})

    assert response.status_code == 201


def test_register_user_already_exists(client):
    username = "existinguser"
    password = "securepassword"
    client.post(
        "/auth/register", json={"username": username, "password": password}
    )  # user already in db

    response = client.post("/auth/register", json={"username": username, "password": password})

    assert response.status_code == 409
    assert response.json()["detail"] == f"User with username {username} already exists"


def test_login_user_success(client):
    username = "loginuser"
    password = "securepassword"
    client.post("/auth/register", json={"username": username, "password": password})  # user in db

    response = client.post("/auth/login", json={"username": username, "password": password})

    assert response.status_code == 200
    assert response.json()["access_token"] is not None
    assert response.json()["token_type"] == "bearer"


def test_login_user_invalid_credentials(client):
    username = "invaliduser"
    password = "wrongpassword"

    response = client.post("/auth/login", json={"username": username, "password": password})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials provided"
