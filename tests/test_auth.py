def test_register_and_me(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "nuevo@test.com",
            "full_name": "Nuevo Usuario",
            "password": "password123",
        },
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    assert token

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "nuevo@test.com"
    assert me.json()["role"] == "user"


def test_register_duplicate_email(client):
    payload = {
        "email": "dup@test.com",
        "full_name": "Duplicado",
        "password": "password123",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_login_ok(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "login@test.com", "full_name": "Login", "password": "password123"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "login@test.com", "password": "password123"},
    )
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "bad@test.com", "full_name": "Bad", "password": "password123"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "bad@test.com", "password": "incorrecta"},
    )
    assert resp.status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401
