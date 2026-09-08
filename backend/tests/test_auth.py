"""Tests: Authentication — login, /me, invalid credentials, token refresh."""
import pytest


class TestLogin:
    def test_login_researcher(self, api):
        token = api.login_as("researcher")
        assert token
        assert len(token) > 20

    def test_login_uro_director(self, api):
        token = api.login_as("uro_director")
        assert token

    def test_login_admin(self, api):
        token = api.login_as("admin")
        assert token

    def test_login_dean(self, api):
        token = api.login_as("dean")
        assert token

    def test_login_uro_staff(self, api):
        token = api.login_as("uro_staff")
        assert token

    def test_login_wrong_password(self, api):
        resp = api._client.post(
            f"{api.prefix}/auth/login",
            data={"username": "researcher1@hau.edu.ph", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, api):
        resp = api._client.post(
            f"{api.prefix}/auth/login",
            data={"username": "nobody@hau.edu.ph", "password": "test123"},
        )
        assert resp.status_code == 401

    def test_login_empty_credentials(self, api):
        resp = api._client.post(
            f"{api.prefix}/auth/login",
            data={"username": "", "password": ""},
        )
        assert resp.status_code in (400, 401, 422)


class TestMe:
    def test_me_returns_user_info(self, api):
        token = api.login_as("researcher")
        resp = api.get("/auth/me", token=token)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "researcher1@hau.edu.ph"
        assert "RESEARCHER" in data["roles"]
        assert data["is_active"] is True

    def test_me_uro_director_roles(self, api):
        token = api.login_as("uro_director")
        resp = api.get("/auth/me", token=token)
        assert resp.status_code == 200
        data = resp.json()
        assert "URO_DIRECTOR" in data["roles"]

    def test_me_admin_roles(self, api):
        token = api.login_as("admin")
        resp = api.get("/auth/me", token=token)
        assert resp.status_code == 200
        data = resp.json()
        assert "ADMIN" in data["roles"]

    def test_me_no_token(self, api):
        resp = api.get("/auth/me")
        assert resp.status_code == 401

    def test_me_invalid_token(self, api):
        resp = api.get("/auth/me", token="invalid.jwt.token")
        assert resp.status_code == 401


class TestTokenRefresh:
    def test_refresh_token(self, api):
        token = api.login_as("researcher")
        resp = api.post("/auth/refresh", json={"token": token})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == "researcher1@hau.edu.ph"

    def test_refresh_invalid_token(self, api):
        resp = api.post("/auth/refresh", json={"token": "garbage"})
        assert resp.status_code == 401
