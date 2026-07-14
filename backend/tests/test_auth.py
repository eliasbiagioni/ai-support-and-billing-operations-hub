"""Authentication tests: login, /me, and failure modes (Phase 7)."""

from __future__ import annotations

from collections.abc import Callable

from app.models.enums import UserRole
from app.models.user import User
from fastapi.testclient import TestClient


def test_login_returns_token_and_user(
    api_client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user("ava@acme.io", password="password123", role=UserRole.admin)
    response = api_client.post(
        "/api/auth/login",
        json={"email": "ava@acme.io", "password": "password123"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "ava@acme.io"
    assert body["user"]["role"] == "admin"


def test_me_requires_and_accepts_token(
    api_client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user("sam@acme.io", password="password123", role=UserRole.support_agent)
    token = api_client.post(
        "/api/auth/login",
        json={"email": "sam@acme.io", "password": "password123"},
    ).json()["access_token"]

    unauth = api_client.get("/api/auth/me")
    assert unauth.status_code == 401
    assert unauth.json()["error"]["code"] == "unauthorized"

    me = api_client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == "sam@acme.io"


def test_login_wrong_password_fails(
    api_client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user("x@acme.io", password="password123")
    response = api_client.post(
        "/api/auth/login",
        json={"email": "x@acme.io", "password": "wrongpass1"},
    )
    assert response.status_code == 401


def test_login_inactive_user_fails(
    api_client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user("disabled@acme.io", password="password123", active=False)
    response = api_client.post(
        "/api/auth/login",
        json={"email": "disabled@acme.io", "password": "password123"},
    )
    assert response.status_code == 401


def test_protected_route_rejects_missing_token(api_client: TestClient) -> None:
    response = api_client.get("/api/customers")
    assert response.status_code == 401
