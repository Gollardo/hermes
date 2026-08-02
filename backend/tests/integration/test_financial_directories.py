from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from time import sleep
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.application.accounts import AccountHasHistoryError, delete_account_without_history
from app.core.config import Settings
from app.core.database import create_database_engine, create_session_factory
from app.main import create_app
from app.modules.accounts.models import Account
from app.modules.categories.contracts import CategoryReferenceError, validate_category_reference
from app.modules.categories.models import Category, CategoryType
from app.modules.categories.service import (
    CategoryHasChildrenError,
    InvalidCategoryParentError,
    create_category,
    set_category_archived,
    update_category,
)
from app.modules.operations.models import AccountMovement, FinancialOperation, OperationType
from app.modules.operations.schemas import OperationCreateRequest
from app.modules.operations.service import create_operation

MASTER_PASSWORD = "correct-master-password"
SETUP_PAYLOAD = {
    "master_password": MASTER_PASSWORD,
    "base_currency": "RUB",
    "timezone": "Europe/Moscow",
}


def csrf_headers(client: TestClient) -> dict[str, str]:
    token = client.cookies.get("XSRF-TOKEN")
    assert token is not None
    return {"X-XSRF-TOKEN": token}


def test_account_lifecycle_balance_and_history_protection(
    postgres_database_settings: Settings,
) -> None:
    app = create_app(postgres_database_settings)
    with TestClient(app) as client:
        assert client.get("/api/v1/accounts").status_code == 401
        assert client.post("/api/v1/setup", json=SETUP_PAYLOAD).status_code == 201
        headers = csrf_headers(client)
        assert (
            client.post(
                "/api/v1/accounts",
                json={"type": "cash", "name": "No CSRF", "initial_balance": "0"},
            ).status_code
            == 403
        )

        invalid_float = client.post(
            "/api/v1/accounts",
            headers=headers,
            json={"type": "cash", "name": "Wallet", "initial_balance": 0.1},
        )
        assert invalid_float.status_code == 422
        invalid_negative = client.post(
            "/api/v1/accounts",
            headers=headers,
            json={"type": "cash", "name": "Wallet", "initial_balance": "-0.01"},
        )
        assert invalid_negative.status_code == 422

        created = client.post(
            "/api/v1/accounts",
            headers=headers,
            json={
                "type": "debit",
                "name": "Main card",
                "description": "Daily spending",
                "initial_balance": "1234.5678",
            },
        )
        assert created.status_code == 201
        account_id = created.json()["id"]
        assert created.json()["balance"] == "1234.5678"
        assert client.get("/api/v1/settings").json()["base_currency_locked"] is True

        updated = client.put(
            f"/api/v1/accounts/{account_id}",
            headers=headers,
            json={"type": "savings", "name": "Reserve", "description": None},
        )
        assert updated.status_code == 200
        assert updated.json()["balance"] == "1234.5678"
        assert "initial_balance" not in updated.json()

        assert (
            client.post(f"/api/v1/accounts/{account_id}/archive", headers=headers).json()[
                "archived"
            ]
            is True
        )
        assert (
            client.post(f"/api/v1/accounts/{account_id}/restore", headers=headers).json()[
                "archived"
            ]
            is False
        )
        blocked = client.delete(f"/api/v1/accounts/{account_id}", headers=headers)
        assert blocked.status_code == 409
        assert blocked.json()["detail"]["code"] == "account_has_history"

        with app.state.session_factory() as session:
            assert session.scalar(select(func.count()).select_from(Account)) == 1
            assert session.scalar(select(func.count()).select_from(FinancialOperation)) == 1
            movement = session.scalar(select(AccountMovement))
            operation = session.scalar(select(FinancialOperation))
            assert movement is not None and str(movement.amount) == "1234.5678"
            assert operation is not None and operation.type == OperationType.BALANCE_ADJUSTMENT


def test_empty_account_can_be_deleted(postgres_database_settings: Settings) -> None:
    with TestClient(create_app(postgres_database_settings)) as client:
        assert client.post("/api/v1/setup", json=SETUP_PAYLOAD).status_code == 201
        headers = csrf_headers(client)
        created = client.post(
            "/api/v1/accounts",
            headers=headers,
            json={"type": "cash", "name": "Temporary", "initial_balance": "0"},
        )
        account_id = created.json()["id"]
        assert client.delete(f"/api/v1/accounts/{account_id}", headers=headers).status_code == 204


def test_account_delete_waits_for_concurrent_posting_history(
    postgres_database_settings: Settings,
) -> None:
    app = create_app(postgres_database_settings)
    with TestClient(app) as client:
        assert client.post("/api/v1/setup", json=SETUP_PAYLOAD).status_code == 201
        headers = csrf_headers(client)
        account_id = UUID(
            client.post(
                "/api/v1/accounts",
                headers=headers,
                json={"type": "cash", "name": "Race", "initial_balance": "0"},
            ).json()["id"]
        )
        category_id = UUID(
            client.post(
                "/api/v1/categories",
                headers=headers,
                json={"type": "income", "name": "Concurrent income"},
            ).json()["id"]
        )

    engine = create_database_engine(postgres_database_settings)
    factory = create_session_factory(engine)
    posting_ready = Event()
    allow_post_commit = Event()
    deletion_started = Event()

    def post_income() -> str:
        with factory.begin() as session:
            create_operation(
                session,
                OperationCreateRequest(
                    type="income",
                    occurred_on="2026-08-02",
                    amount="10",
                    account_id=account_id,
                    category_id=category_id,
                ),
            )
            posting_ready.set()
            assert allow_post_commit.wait(timeout=5)
        return "posted"

    def delete_account() -> str:
        assert posting_ready.wait(timeout=5)
        deletion_started.set()
        try:
            with factory.begin() as session:
                delete_account_without_history(session, account_id)
        except AccountHasHistoryError:
            return "history"
        return "deleted"

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            post_result = executor.submit(post_income)
            delete_result = executor.submit(delete_account)
            assert deletion_started.wait(timeout=5)
            sleep(0.1)
            assert not delete_result.done()
            allow_post_commit.set()
            assert post_result.result(timeout=5) == "posted"
            assert delete_result.result(timeout=5) == "history"
    finally:
        engine.dispose()


def test_category_tree_edit_and_archive_rules(postgres_database_settings: Settings) -> None:
    app = create_app(postgres_database_settings)
    with TestClient(app) as client:
        assert client.get("/api/v1/categories").status_code == 401
        assert client.post("/api/v1/setup", json=SETUP_PAYLOAD).status_code == 201
        headers = csrf_headers(client)
        assert (
            client.post(
                "/api/v1/categories", json={"type": "expense", "name": "No CSRF"}
            ).status_code
            == 403
        )
        parent = client.post(
            "/api/v1/categories",
            headers=headers,
            json={"type": "expense", "name": "Home"},
        )
        assert parent.status_code == 201
        parent_id = parent.json()["id"]
        assert client.get("/api/v1/settings").json()["base_currency_locked"] is False
        child = client.post(
            "/api/v1/categories",
            headers=headers,
            json={"type": "expense", "name": "Utilities", "parent_id": parent_id},
        )
        assert child.status_code == 201
        child_id = child.json()["id"]

        edited = client.put(
            f"/api/v1/categories/{child_id}",
            headers=headers,
            json={
                "type": "expense",
                "name": "Household utilities",
                "description": "Monthly bills",
                "parent_id": parent_id,
            },
        )
        assert edited.status_code == 200
        assert edited.json()["name"] == "Household utilities"

        third_level = client.post(
            "/api/v1/categories",
            headers=headers,
            json={"type": "expense", "name": "Electricity", "parent_id": child_id},
        )
        assert third_level.status_code == 409

        wrong_type = client.post(
            "/api/v1/categories",
            headers=headers,
            json={"type": "income", "name": "Salary", "parent_id": parent_id},
        )
        assert wrong_type.status_code == 409
        cycle = client.put(
            f"/api/v1/categories/{parent_id}",
            headers=headers,
            json={
                "type": "expense",
                "name": "Home",
                "description": None,
                "parent_id": child_id,
            },
        )
        assert cycle.status_code == 409
        blocked_parent = client.post(f"/api/v1/categories/{parent_id}/archive", headers=headers)
        assert blocked_parent.status_code == 409

        archived_child = client.post(f"/api/v1/categories/{child_id}/archive", headers=headers)
        assert archived_child.status_code == 200
        assert archived_child.json()["archived"] is True
        archived_parent = client.post(f"/api/v1/categories/{parent_id}/archive", headers=headers)
        assert archived_parent.status_code == 200
        restore_child = client.post(f"/api/v1/categories/{child_id}/restore", headers=headers)
        assert restore_child.status_code == 409

        listed = client.get("/api/v1/categories").json()
        assert {UUID(item["id"]) for item in listed} == {UUID(parent_id), UUID(child_id)}
        assert client.get("/api/v1/categories?include_archived=false").json() == []

        with app.state.session_factory() as session:
            with pytest.raises(CategoryReferenceError):
                validate_category_reference(
                    session, UUID(child_id), expected_type=CategoryType.EXPENSE
                )
            historical = validate_category_reference(
                session,
                UUID(child_id),
                expected_type=CategoryType.EXPENSE,
                allow_archived=True,
            )
            assert historical.id == UUID(child_id)
            assert historical.archived is True


def test_concurrent_category_reparenting_cannot_create_cycle(
    postgres_database_settings: Settings,
) -> None:
    app = create_app(postgres_database_settings)
    with TestClient(app) as client:
        assert client.post("/api/v1/setup", json=SETUP_PAYLOAD).status_code == 201
        headers = csrf_headers(client)
        first_id = UUID(
            client.post(
                "/api/v1/categories",
                headers=headers,
                json={"type": "expense", "name": "First"},
            ).json()["id"]
        )
        second_id = UUID(
            client.post(
                "/api/v1/categories",
                headers=headers,
                json={"type": "expense", "name": "Second"},
            ).json()["id"]
        )

        engine = create_database_engine(postgres_database_settings)
        factory = create_session_factory(engine)
        start = Barrier(2)

        def reparent(category_id: UUID, parent_id: UUID) -> str:
            start.wait()
            try:
                with factory.begin() as session:
                    update_category(
                        session,
                        category_id,
                        type=CategoryType.EXPENSE,
                        name=str(category_id),
                        description=None,
                        parent_id=parent_id,
                        has_financial_history=False,
                    )
            except InvalidCategoryParentError:
                return "rejected"
            return "updated"

        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(
                    executor.map(
                        lambda pair: reparent(*pair),
                        [(first_id, second_id), (second_id, first_id)],
                    )
                )
            assert sorted(results) == ["rejected", "updated"]
            with factory() as session:
                first = session.get(Category, first_id)
                second = session.get(Category, second_id)
                assert first is not None and second is not None
                assert not (first.parent_id == second_id and second.parent_id == first_id)

            race_parent_id = UUID(
                client.post(
                    "/api/v1/categories",
                    headers=headers,
                    json={"type": "expense", "name": "Archive race"},
                ).json()["id"]
            )
            archive_start = Barrier(2)

            def archive_parent() -> str:
                archive_start.wait()
                try:
                    with factory.begin() as session:
                        set_category_archived(session, race_parent_id, archived=True)
                except CategoryHasChildrenError:
                    return "rejected"
                return "updated"

            def create_child() -> str:
                archive_start.wait()
                try:
                    with factory.begin() as session:
                        create_category(
                            session,
                            type=CategoryType.EXPENSE,
                            name="Concurrent child",
                            description=None,
                            parent_id=race_parent_id,
                        )
                except InvalidCategoryParentError:
                    return "rejected"
                return "updated"

            with ThreadPoolExecutor(max_workers=2) as executor:
                archive_result = executor.submit(archive_parent)
                child_result = executor.submit(create_child)
                assert sorted([archive_result.result(), child_result.result()]) == [
                    "rejected",
                    "updated",
                ]

            with factory() as session:
                parent = session.get(Category, race_parent_id)
                active_child = session.scalar(
                    select(Category.id).where(
                        Category.parent_id == race_parent_id,
                        Category.archived_at.is_(None),
                    )
                )
                assert parent is not None
                assert not (parent.archived_at is not None and active_child is not None)
        finally:
            engine.dispose()
