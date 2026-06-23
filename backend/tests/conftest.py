import os
from collections.abc import Generator
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

# These must be set before importing main/app modules, because config, security,
# and database objects are initialized at import time.
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_PUBLISHABLE_KEY", "test-publishable-key")

from app.database import get_session  # noqa: E402
from app.middleware.auth import get_current_user  # noqa: E402
from main import app as fastapi_app  # noqa: E402


TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_ORGANISATION_ID = "00000000-0000-0000-0000-000000000010"


@pytest.fixture
def app() -> Generator:
    fastapi_app.dependency_overrides.clear()
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client(app) -> Generator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def fake_user() -> dict:
    return {
        "sub": TEST_USER_ID,
        "email": "student@example.com",
        "aud": "authenticated",
        "role": "authenticated",
    }


@pytest.fixture
def fake_event():
    def build_event(**overrides):
        starts_at = datetime(2026, 6, 22, 18, 0)
        values = {
            "status": "active",
            "capacity": 30,
            "spots_remaining": 10,
            "starts_at": starts_at,
            "ends_at": starts_at + timedelta(hours=2),
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    return build_event


@pytest.fixture
def authenticated_client(app, fake_user) -> Generator[TestClient]:
    app.dependency_overrides[get_current_user] = lambda: fake_user

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def override_db_session(app):
    def override(session):
        def get_test_session():
            yield session

        app.dependency_overrides[get_session] = get_test_session
        return session

    return override


@pytest.fixture
def fail_if_db_is_used(app):
    def get_test_session():
        raise AssertionError("This test should not connect to the database")
        yield

    app.dependency_overrides[get_session] = get_test_session
