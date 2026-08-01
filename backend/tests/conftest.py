from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import AppEnvironment, Settings
from app.main import create_app


@pytest.fixture
def application() -> FastAPI:
    return create_app(
        Settings(
            app_env=AppEnvironment.TEST,
            database_name="hermes_test",
            database_password="test-only-password",
        )
    )


@pytest.fixture
def client(application: FastAPI) -> Iterator[TestClient]:
    with TestClient(application) as test_client:
        yield test_client
