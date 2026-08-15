from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from decimal import Decimal
from threading import Barrier
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_database_engine, create_session_factory
from app.main import create_app
from app.modules.operations import service as operations_service
from app.modules.operations.models import AccountMovement, FinancialOperation
from app.modules.operations.schemas import OperationCreateRequest
from app.modules.operations.service import InsufficientBalanceError, create_operation

MASTER_PASSWORD = "correct-master-password"
SETUP_PAYLOAD = {
    "master_password": MASTER_PASSWORD,
    "base_currency": "RUB",
    "timezone": "Europe/Moscow",
}


def _headers(client: TestClient) -> dict[str, str]:
    token = client.cookies.get("XSRF-TOKEN")
    assert token is not None
    return {"X-XSRF-TOKEN": token}


def _account(client: TestClient, headers: dict[str, str], name: str, balance: str) -> str:
    response = client.post(
        "/api/v1/accounts",
        headers=headers,
        json={"type": "debit", "name": name, "initial_balance": balance},
    )
    assert response.status_code == 201
    return str(response.json()["id"])


def _category(client: TestClient, headers: dict[str, str], name: str, type: str) -> str:
    response = client.post("/api/v1/categories", headers=headers, json={"type": type, "name": name})
    assert response.status_code == 201
    return str(response.json()["id"])


def test_complete_operation_lifecycle_and_journal_filters(
    postgres_database_settings: Settings,
) -> None:
    app = create_app(postgres_database_settings)
    with TestClient(app) as client:
        assert client.post("/api/v1/setup", json=SETUP_PAYLOAD).status_code == 201
        headers = _headers(client)
        source_id = _account(client, headers, "Main", "100")
        target_id = _account(client, headers, "Savings", "10")
        income_category = _category(client, headers, "Salary", "income")
        expense_category = _category(client, headers, "Food", "expense")
        expense_leaf_response = client.post(
            "/api/v1/categories",
            headers=headers,
            json={
                "type": "expense",
                "name": "Groceries",
                "parent_id": expense_category,
            },
        )
        assert expense_leaf_response.status_code == 201
        expense_leaf = str(expense_leaf_response.json()["id"])

        income = client.post(
            "/api/v1/operations",
            headers=headers,
            json={
                "type": "income",
                "occurred_on": "2026-08-01",
                "amount": "50.0000",
                "description": "August salary",
                "account_id": source_id,
                "category_id": income_category,
            },
        )
        assert income.status_code == 201
        assert income.json()["amount"] == "50.0000"
        locked_category_type = client.put(
            f"/api/v1/categories/{income_category}",
            headers=headers,
            json={"type": "expense", "name": "Salary", "parent_id": None},
        )
        assert locked_category_type.status_code == 409
        assert locked_category_type.json()["detail"]["code"] == "category_type_has_history"

        expense = client.post(
            "/api/v1/operations",
            headers=headers,
            json={
                "type": "expense",
                "occurred_on": "2026-08-02",
                "amount": "70",
                "account_id": source_id,
                "category_id": expense_leaf,
            },
        )
        assert expense.status_code == 201

        transfer = client.post(
            "/api/v1/operations",
            headers=headers,
            json={
                "type": "transfer",
                "occurred_on": "2026-08-02",
                "amount": "25",
                "description": "Reserve",
                "account_id": source_id,
                "destination_account_id": target_id,
            },
        )
        assert transfer.status_code == 201
        transfer_body = transfer.json()
        assert len(transfer_body["movements"]) == 2
        assert sum(Decimal(item["amount"]) for item in transfer_body["movements"]) == 0

        adjustment = client.post(
            "/api/v1/operations",
            headers=headers,
            json={
                "type": "balance_adjustment",
                "occurred_on": "2026-08-02",
                "amount": "5.5",
                "account_id": target_id,
                "reason": "Bank reconciliation",
            },
        )
        assert adjustment.status_code == 201
        assert adjustment.json()["reason"] == "Bank reconciliation"

        accounts = {item["id"]: item["balance"] for item in client.get("/api/v1/accounts").json()}
        assert accounts[source_id] == "55.0000"
        assert accounts[target_id] == "40.5000"

        journal = client.get(
            f"/api/v1/operations?account_id={source_id}&occurred_from=2026-08-02&page_size=2"
        )
        assert journal.status_code == 200
        assert journal.json()["total"] == 3
        assert journal.json()["total_amount"] == "5.0000"
        assert len(journal.json()["items"]) == 2
        category_summary = client.get(
            "/api/v1/operations/category-summary?from_on=2026-08-01&through_on=2026-08-31"
        )
        assert category_summary.status_code == 200
        assert category_summary.json()["income"][0]["amount"] == "50.0000"
        assert category_summary.json()["expense"][0]["amount"] == "70.0000"
        assert category_summary.json()["expense"][0]["category_id"] == expense_category
        assert (
            client.get(f"/api/v1/operations?type=expense&category_id={expense_category}").json()[
                "total"
            ]
            == 1
        )
        assert (
            client.get(f"/api/v1/operations?type=expense&category_id={expense_leaf}").json()[
                "total"
            ]
            == 1
        )
        assert (
            client.get(
                "/api/v1/operations/category-summary?from_on=2026-08-31&through_on=2026-08-01"
            ).status_code
            == 422
        )

        updated_income = client.put(
            f"/api/v1/operations/{income.json()['id']}",
            headers=headers,
            json={
                "type": "income",
                "occurred_on": "2026-08-01",
                "amount": "50",
                "description": "Reviewed salary",
                "account_id": source_id,
                "category_id": income_category,
                "version": 1,
            },
        )
        assert updated_income.status_code == 200
        assert updated_income.json()["version"] == 2
        updated_expense = client.put(
            f"/api/v1/operations/{expense.json()['id']}",
            headers=headers,
            json={
                "type": "expense",
                "occurred_on": "2026-08-02",
                "amount": "65",
                "account_id": source_id,
                "category_id": expense_leaf,
                "version": 1,
            },
        )
        assert updated_expense.status_code == 200
        assert updated_expense.json()["version"] == 2

        updated_transfer = client.put(
            f"/api/v1/operations/{transfer_body['id']}",
            headers=headers,
            json={
                "type": "transfer",
                "occurred_on": "2026-08-03",
                "amount": "40",
                "description": "Larger reserve",
                "account_id": source_id,
                "destination_account_id": target_id,
                "version": transfer_body["version"],
            },
        )
        assert updated_transfer.status_code == 200
        assert updated_transfer.json()["version"] == 2
        stale = client.put(
            f"/api/v1/operations/{transfer_body['id']}",
            headers=headers,
            json={
                "type": "transfer",
                "occurred_on": "2026-08-03",
                "amount": "20",
                "account_id": source_id,
                "destination_account_id": target_id,
                "version": 1,
            },
        )
        assert stale.status_code == 409
        assert stale.json()["detail"]["code"] == "operation_conflict"

        too_large = client.post(
            "/api/v1/operations",
            headers=headers,
            json={
                "type": "expense",
                "occurred_on": "2026-08-03",
                "amount": "1000",
                "account_id": source_id,
                "category_id": expense_category,
            },
        )
        assert too_large.status_code == 409
        assert too_large.json()["detail"]["code"] == "insufficient_balance"

        blocked_delete = client.delete(
            f"/api/v1/operations/{income.json()['id']}?version=2", headers=headers
        )
        assert blocked_delete.status_code == 409
        assert blocked_delete.json()["detail"]["code"] == "insufficient_balance"
        deleted = client.delete(
            f"/api/v1/operations/{expense.json()['id']}?version=2", headers=headers
        )
        assert deleted.status_code == 204
        assert (
            client.delete(
                f"/api/v1/operations/{transfer_body['id']}?version=2", headers=headers
            ).status_code
            == 204
        )
        assert (
            client.delete(
                f"/api/v1/operations/{adjustment.json()['id']}?version=1", headers=headers
            ).status_code
            == 204
        )
        assert (
            client.delete(
                f"/api/v1/operations/{income.json()['id']}?version=2", headers=headers
            ).status_code
            == 204
        )

        with app.state.session_factory() as session:
            assert session.get(FinancialOperation, UUID(expense.json()["id"])) is None
            assert session.get(FinancialOperation, UUID(transfer_body["id"])) is None
            assert session.get(FinancialOperation, UUID(adjustment.json()["id"])) is None
            assert session.get(FinancialOperation, UUID(income.json()["id"])) is None
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(AccountMovement)
                    .where(AccountMovement.operation_id == UUID(expense.json()["id"]))
                )
                == 0
            )
        balances = {item["id"]: item["balance"] for item in client.get("/api/v1/accounts").json()}
        assert balances[source_id] == "100.0000"
        assert balances[target_id] == "10.0000"


def test_transfer_failure_after_first_movement_rolls_back_everything(
    postgres_database_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = create_app(postgres_database_settings)
    with TestClient(app) as client:
        assert client.post("/api/v1/setup", json=SETUP_PAYLOAD).status_code == 201
        headers = _headers(client)
        source_id = _account(client, headers, "Source", "10")
        target_id = _account(client, headers, "Target", "0")
        with app.state.session_factory() as session:
            before_operations = session.scalar(select(func.count()).select_from(FinancialOperation))
            before_movements = session.scalar(select(func.count()).select_from(AccountMovement))

        def add_one_then_fail(
            database_session: Session, operation_id: UUID, amounts: dict[UUID, Decimal]
        ) -> None:
            account_id, amount = next(iter(amounts.items()))
            database_session.add(
                AccountMovement(operation_id=operation_id, account_id=account_id, amount=amount)
            )
            database_session.flush()
            raise RuntimeError("injected failure after first movement")

        monkeypatch.setattr(operations_service, "_add_movements", add_one_then_fail)
        with pytest.raises(RuntimeError, match="injected failure"):
            client.post(
                "/api/v1/operations",
                headers=headers,
                json={
                    "type": "transfer",
                    "occurred_on": "2026-08-02",
                    "amount": "1",
                    "account_id": source_id,
                    "destination_account_id": target_id,
                },
            )
        with app.state.session_factory() as session:
            assert (
                session.scalar(select(func.count()).select_from(FinancialOperation))
                == before_operations
            )
            assert (
                session.scalar(select(func.count()).select_from(AccountMovement))
                == before_movements
            )


def test_concurrent_expenses_cannot_overdraw_account(
    postgres_database_settings: Settings,
) -> None:
    app = create_app(postgres_database_settings)
    with TestClient(app) as client:
        assert client.post("/api/v1/setup", json=SETUP_PAYLOAD).status_code == 201
        headers = _headers(client)
        account_id = UUID(_account(client, headers, "Shared", "100"))
        category_id = UUID(_category(client, headers, "Food", "expense"))

    engine = create_database_engine(postgres_database_settings)
    factory = create_session_factory(engine)
    start = Barrier(2)
    payload = OperationCreateRequest(
        type="expense",
        occurred_on="2026-08-02",
        amount="80",
        account_id=account_id,
        category_id=category_id,
    )

    def spend() -> str:
        start.wait()
        try:
            with factory.begin() as session:
                create_operation(session, payload)
        except InsufficientBalanceError:
            return "rejected"
        return "posted"

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: spend(), range(2)))
        assert sorted(results) == ["posted", "rejected"]
        with factory() as session:
            balance = session.scalar(
                select(func.coalesce(func.sum(AccountMovement.amount), 0)).where(
                    AccountMovement.account_id == account_id
                )
            )
            assert Decimal(balance or 0) == Decimal("20.0000")
    finally:
        engine.dispose()


def test_existing_alpha2_initial_adjustment_upgrades_to_journal(
    postgres_database_settings: Settings,
) -> None:
    command.downgrade(Config("alembic.ini"), "0003_accounts_categories")
    account_id = UUID("10000000-0000-0000-0000-000000000001")
    operation_id = UUID("20000000-0000-0000-0000-000000000001")
    movement_id = UUID("30000000-0000-0000-0000-000000000001")
    now = datetime(2026, 8, 1, 22, 30, tzinfo=UTC)
    engine = create_database_engine(postgres_database_settings)
    factory = create_session_factory(engine)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO application_settings "
                    "(id, base_currency, timezone, base_currency_locked_at, "
                    "created_at, updated_at) "
                    "VALUES (1, 'RUB', 'Europe/Moscow', NULL, :now, :now)"
                ),
                {"now": now},
            )
            connection.execute(
                text(
                    "INSERT INTO accounts "
                    "(id, type, name, description, archived_at, created_at, updated_at) "
                    "VALUES (:id, CAST('cash' AS account_type), "
                    "'Legacy wallet', NULL, NULL, :now, :now)"
                ),
                {"id": account_id, "now": now},
            )
            connection.execute(
                text(
                    "INSERT INTO financial_operations "
                    "(id, type, description, occurred_at, created_at) "
                    "VALUES (:id, CAST('balance_adjustment' AS financial_operation_type), "
                    "'Initial balance', :now, :now)"
                ),
                {"id": operation_id, "now": now},
            )
            connection.execute(
                text(
                    "INSERT INTO account_movements (id, operation_id, account_id, amount) "
                    "VALUES (:id, :operation_id, :account_id, 42.5000)"
                ),
                {"id": movement_id, "operation_id": operation_id, "account_id": account_id},
            )

        command.upgrade(Config("alembic.ini"), "head")
        with factory() as session:
            operation = session.get(FinancialOperation, operation_id)
            assert operation is not None
            assert operation.occurred_on == date(2026, 8, 2)
            assert operation.reason == "Initial balance"
            assert operation.version == 1
            assert session.scalar(select(func.sum(AccountMovement.amount))) == Decimal("42.5000")
    finally:
        engine.dispose()


def test_alpha3_data_with_optional_description_can_downgrade(
    postgres_database_settings: Settings,
) -> None:
    app = create_app(postgres_database_settings)
    with TestClient(app) as client:
        assert client.post("/api/v1/setup", json=SETUP_PAYLOAD).status_code == 201
        headers = _headers(client)
        account_id = _account(client, headers, "Main", "10")
        category_id = _category(client, headers, "Food", "expense")
        response = client.post(
            "/api/v1/operations",
            headers=headers,
            json={
                "type": "expense",
                "occurred_on": "2026-08-02",
                "amount": "1",
                "account_id": account_id,
                "category_id": category_id,
            },
        )
        assert response.status_code == 201

    command.downgrade(Config("alembic.ini"), "0003_accounts_categories")
    with app.state.database_engine.connect() as connection:
        description = connection.scalar(
            text("SELECT description FROM financial_operations WHERE id = :id"),
            {"id": UUID(response.json()["id"])},
        )
        assert description == "Legacy expense"
