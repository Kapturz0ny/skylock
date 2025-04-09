def test_register_user_success(client):
    username = "testuser"
    password = "securepassword"

    response = client.post("/auth/register", json={"username": username, "password": password})

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
