"""Admin-only user management tests (Phase 7). No public registration."""

from __future__ import annotations

from collections.abc import Callable

from app.models.enums import UserRole
from app.models.user import User
from fastapi.testclient import TestClient


def _login(client: TestClient, email: str, password: str = "password123") -> str:
    response = client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_create_and_list_users(
    api_client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user("admin@acme.io", role=UserRole.admin)
    token = _login(api_client, "admin@acme.io")

    created = api_client.post(
        "/api/users",
        headers=_auth(token),
        json={
            "name": "New Agent",
            "email": "new.agent@acme.io",
            "password": "password123",
            "role": "support_agent",
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["email"] == "new.agent@acme.io"

    listing = api_client.get("/api/users", headers=_auth(token))
    assert listing.status_code == 200
    emails = {item["email"] for item in listing.json()["items"]}
    assert {"admin@acme.io", "new.agent@acme.io"} <= emails


def test_non_admin_cannot_manage_users(
    api_client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user("agent@acme.io", role=UserRole.support_agent)
    token = _login(api_client, "agent@acme.io")

    response = api_client.post(
        "/api/users",
        headers=_auth(token),
        json={
            "name": "Nope",
            "email": "nope@acme.io",
            "password": "password123",
        },
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"

    assert api_client.get("/api/users", headers=_auth(token)).status_code == 403


def test_admin_can_reset_password(
    api_client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user("admin2@acme.io", role=UserRole.admin)
    target = make_user("target@acme.io", role=UserRole.support_agent)
    token = _login(api_client, "admin2@acme.io")

    reset = api_client.post(
        f"/api/users/{target.id}/reset-password",
        headers=_auth(token),
        json={"new_password": "brandnew123"},
    )
    assert reset.status_code == 200, reset.text

    assert _login(api_client, "target@acme.io", "brandnew123")
