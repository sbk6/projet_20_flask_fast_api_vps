import pytest


def test_register_success(client):
    resp = client.post("/auth/register", json={
        "email": "new@test.com",
        "username": "newuser",
        "password": "Password123!",
        "full_name": "New User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@test.com"
    assert data["username"] == "newuser"
    assert "hashed_password" not in data


def test_register_duplicate_email(client, regular_user):
    resp = client.post("/auth/register", json={
        "email": "user@test.com",
        "username": "another",
        "password": "Password123!",
    })
    assert resp.status_code == 409


def test_register_duplicate_username(client, regular_user):
    resp = client.post("/auth/register", json={
        "email": "another@test.com",
        "username": "testuser",
        "password": "Password123!",
    })
    assert resp.status_code == 409


def test_register_invalid_email(client):
    resp = client.post("/auth/register", json={
        "email": "not-an-email",
        "username": "validuser",
        "password": "Password123!",
    })
    assert resp.status_code == 422


def test_register_short_password(client):
    resp = client.post("/auth/register", json={
        "email": "test@test.com",
        "username": "validuser",
        "password": "short",
    })
    assert resp.status_code == 422


def test_login_success(client, regular_user):
    resp = client.post("/auth/login", json={"email": "user@test.com", "password": "User123!"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, regular_user):
    resp = client.post("/auth/login", json={"email": "user@test.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/auth/login", json={"email": "ghost@test.com", "password": "Whatever123!"})
    assert resp.status_code == 401


def test_get_me(client, auth_headers_user):
    resp = client.get("/auth/me", headers=auth_headers_user)
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@test.com"


def test_get_me_no_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code in (401, 403)


def test_refresh_token(client, regular_user):
    login = client.post("/auth/login", json={"email": "user@test.com", "password": "User123!"})
    refresh_token = login.json()["refresh_token"]
    resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_refresh_with_access_token_fails(client, user_token):
    resp = client.post("/auth/refresh", json={"refresh_token": user_token})
    assert resp.status_code == 401
