import argon2

from skylock.database.models import UserEntity

def test_register_user_success(client):
    username = "testuser"
    password = "securepassword"
    email = "test@example.com"

    response = client.post("/auth/register", json={"username": username, "password": password, "email": email})
    assert response.status_code == 201


def test_register_user_already_exists(client, db_session):
    username = "existinguser"
    password = "securepassword"
    email = "test@example.com"

    existing_user = UserEntity(
        id=1,
        username=username,
        password=password,
        email=email
    )
    db_session.add(existing_user)
    db_session.commit()

    response = client.post("/auth/register", json={"username": username, "password": password, "email": email})

    assert response.status_code == 409
    assert response.json()["detail"] == f"User with given username/email already exists"


def test_login_user_success(client, db_session):
    username = "loginuser"
    password = "securepassword"
    email = "test@example.com"

    existing_user = UserEntity(
        id=1,
        username=username,
        password=argon2.PasswordHasher().hash(password),
        email=email
    )

    db_session.add(existing_user)
    db_session.commit()

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
