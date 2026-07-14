"""PyTest fixtures: in-memory SQLite DB, dependency overrides, and mocked user.

Tests run against SQLite for speed (PRD 14.1). The app's DB session and the
mocked ``current_user`` dependency are overridden so no external services or a
live Postgres are required in CI.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models import Base, User
from app.models.enums import UserRole
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def seeded_user(db_session: Session) -> User:
    user = User(
        name="Test Agent",
        email="agent@test.local",
        role=UserRole.support_agent,
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def client(db_session: Session, seeded_user: User) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        yield db_session

    def override_current_user() -> User:
        return seeded_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def customer_id(client: TestClient) -> str:
    response = client.post(
        "/api/customers",
        json={"company_name": "Acme Co", "email": "ops@acme.example"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]
