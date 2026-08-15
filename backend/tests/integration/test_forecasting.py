from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from decimal import Decimal
from threading import Event
from typing import cast
from uuid import UUID

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.main import create_app
from app.modules.operations.ledger import account_balances as read_account_balances
from app.modules.scheduling.models import ExpectedOccurrence

MASTER_PASSWORD = "correct-master-password"
SETUP = {
    "master_password": MASTER_PASSWORD,
    "base_currency": "RUB",
    "timezone": "Europe/Moscow",
}


def csrf(client: TestClient) -> dict[str, str]:
    return {"X-XSRF-TOKEN": str(client.cookies.get("XSRF-TOKEN"))}


def test_forecast_api_uses_actual_balances_and_only_actionable_future_occurrences(
    postgres_database_settings: Settings,
) -> None:
    app = create_app(postgres_database_settings)
    with TestClient(app) as client:
        assert client.get("/api/v1/forecast").status_code == 401
        assert client.post("/api/v1/setup", json=SETUP).status_code == 201
        headers = csrf(client)
        source = client.post(
            "/api/v1/accounts",
            headers=headers,
            json={"type": "debit", "name": "Main", "initial_balance": "100"},
        ).json()["id"]
        target = client.post(
            "/api/v1/accounts",
            headers=headers,
            json={"type": "savings", "name": "Savings", "initial_balance": "20"},
        ).json()["id"]
        income_category = client.post(
            "/api/v1/categories",
            headers=headers,
            json={"type": "income", "name": "Salary"},
        ).json()["id"]
        expense_category = client.post(
            "/api/v1/categories",
            headers=headers,
            json={"type": "expense", "name": "Food"},
        ).json()["id"]
        materialized = client.post("/api/v1/scheduling/materialize", headers=headers).json()
        today = date.fromisoformat(materialized["horizon_from"])

        def create_rule(payload: dict[str, object]) -> dict[str, object]:
            response = client.post("/api/v1/scheduling/rules", headers=headers, json=payload)
            assert response.status_code == 201
            return cast(dict[str, object], response.json())

        common = {"frequency": "daily", "start_on": today.isoformat(), "end_on": today.isoformat()}
        income = create_rule(
            {
                **common,
                "type": "income",
                "amount": "30",
                "description": "Salary",
                "account_id": source,
                "category_id": income_category,
            }
        )
        expense = create_rule(
            {
                **common,
                "type": "expense",
                "amount": "50",
                "description": "Food",
                "account_id": source,
                "category_id": expense_category,
            }
        )
        create_rule(
            {
                **common,
                "type": "transfer",
                "amount": "25",
                "description": "Move",
                "account_id": source,
                "destination_account_id": target,
            }
        )
        occurrences = client.get(
            "/api/v1/scheduling/occurrences?page_size=20",
        ).json()["items"]
        income_occurrence = next(item for item in occurrences if item["rule_id"] == income["id"])
        assert (
            client.post(
                f"/api/v1/scheduling/occurrences/{income_occurrence['id']}/confirm",
                headers=headers,
                json={"version": income_occurrence["version"]},
            ).status_code
            == 200
        )

        combined = client.get("/api/v1/forecast?horizon=week")
        assert combined.status_code == 200
        body = combined.json()
        assert body["starting_balance"] == "150.0000"
        assert body["ending_balance"] == "100.0000"
        assert body["expected_income"] == "0"
        assert body["expected_expense"] == "50.0000"
        assert body["first_negative_on"] is None
        assert body["first_negative_balance"] is None
        assert any(
            event["type"] == "transfer" and event["effect"] == "0"
            for point in body["points"]
            for event in point["events"]
        )

        source_forecast = client.get(f"/api/v1/forecast?horizon=week&account_id={source}").json()
        assert source_forecast["starting_balance"] == "130.0000"
        assert source_forecast["ending_balance"] == "55.0000"

        missing = client.get("/api/v1/forecast?account_id=00000000-0000-0000-0000-000000000099")
        assert missing.status_code == 404
        assert missing.json()["detail"]["code"] == "forecast_account_not_found"

        postponed = next(item for item in occurrences if item["rule_id"] == expense["id"])
        new_due = today + timedelta(days=2)
        assert (
            client.post(
                f"/api/v1/scheduling/occurrences/{postponed['id']}/postpone",
                headers=headers,
                json={"version": postponed["version"], "due_on": new_due.isoformat()},
            ).status_code
            == 200
        )
        moved = client.get(f"/api/v1/forecast?horizon=week&account_id={source}").json()
        food = next(
            event
            for point in moved["points"]
            for event in point["events"]
            if event["description"] == "Food"
        )
        assert food["due_on"] == new_due.isoformat()


def test_forecast_defaults_to_free_money_and_can_include_reserves(
    postgres_database_settings: Settings,
) -> None:
    app = create_app(postgres_database_settings)
    with TestClient(app) as client:
        assert client.post("/api/v1/setup", json=SETUP).status_code == 201
        headers = csrf(client)
        account = client.post(
            "/api/v1/accounts",
            headers=headers,
            json={"type": "debit", "name": "Main", "initial_balance": "100"},
        ).json()["id"]
        fund = client.post(
            "/api/v1/funds",
            headers=headers,
            json={"name": "Reserve", "allocation_percentage": "20"},
        ).json()
        allocation = client.post(
            "/api/v1/funds/allocations",
            headers=headers,
            json={
                "account_id": account,
                "amount": "30",
                "occurred_on": "2026-08-15",
                "allocations": [{"fund_id": fund["id"], "amount": "30"}],
            },
        )
        assert allocation.status_code == 201

        free = client.get("/api/v1/forecast?horizon=week")
        total = client.get("/api/v1/forecast?horizon=week&balance_mode=total")

        assert free.status_code == total.status_code == 200
        assert free.json()["balance_mode"] == "free"
        assert free.json()["starting_balance"] == "70.0000"
        assert total.json()["balance_mode"] == "total"
        assert total.json()["starting_balance"] == "100.0000"


def test_concurrent_confirmation_cannot_be_counted_as_actual_and_planned(
    postgres_database_settings: Settings,
    monkeypatch: MonkeyPatch,
) -> None:
    app = create_app(postgres_database_settings)
    with TestClient(app) as client:
        assert client.post("/api/v1/setup", json=SETUP).status_code == 201
        headers = csrf(client)
        account = client.post(
            "/api/v1/accounts",
            headers=headers,
            json={"type": "debit", "name": "Main", "initial_balance": "100"},
        ).json()["id"]
        category = client.post(
            "/api/v1/categories",
            headers=headers,
            json={"type": "income", "name": "Salary"},
        ).json()["id"]
        materialized = client.post("/api/v1/scheduling/materialize", headers=headers).json()
        today = str(materialized["horizon_from"])
        rule = client.post(
            "/api/v1/scheduling/rules",
            headers=headers,
            json={
                "frequency": "daily",
                "start_on": today,
                "end_on": today,
                "type": "income",
                "amount": "30",
                "description": "Salary",
                "account_id": account,
                "category_id": category,
            },
        ).json()
        occurrence = next(
            item
            for item in client.get("/api/v1/scheduling/occurrences?page_size=20").json()["items"]
            if item["rule_id"] == rule["id"]
        )

    from app.modules.forecasting import service as forecasting_service
    from app.modules.scheduling import service as scheduling_service

    forecast_has_snapshot = Event()
    release_forecast = Event()
    confirmation_attempting_lock = Event()
    confirmation_acquired_lock = Event()
    original_get_occurrence = scheduling_service._get_occurrence

    def pause_forecast(session: Session, account_ids: set[UUID]) -> dict[UUID, Decimal]:
        forecast_has_snapshot.set()
        assert release_forecast.wait(timeout=5)
        return read_account_balances(session, account_ids)

    def observe_confirmation_lock(
        session: Session, occurrence_id: UUID, *, lock: bool
    ) -> ExpectedOccurrence:
        confirmation_attempting_lock.set()
        result = original_get_occurrence(session, occurrence_id, lock=lock)
        confirmation_acquired_lock.set()
        return result

    monkeypatch.setattr(forecasting_service, "account_balances", pause_forecast)
    monkeypatch.setattr(scheduling_service, "_get_occurrence", observe_confirmation_lock)

    def forecast_request() -> dict[str, object]:
        with TestClient(app) as concurrent_client:
            assert (
                concurrent_client.post(
                    "/api/v1/auth/login", json={"master_password": MASTER_PASSWORD}
                ).status_code
                == 200
            )
            response = concurrent_client.get("/api/v1/forecast?horizon=week")
            assert response.status_code == 200
            return cast(dict[str, object], response.json())

    def confirm_request() -> int:
        with TestClient(app) as concurrent_client:
            assert (
                concurrent_client.post(
                    "/api/v1/auth/login", json={"master_password": MASTER_PASSWORD}
                ).status_code
                == 200
            )
            return concurrent_client.post(
                f"/api/v1/scheduling/occurrences/{occurrence['id']}/confirm",
                headers=csrf(concurrent_client),
                json={"version": occurrence["version"]},
            ).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        forecast_future = executor.submit(forecast_request)
        assert forecast_has_snapshot.wait(timeout=5)
        confirm_future = executor.submit(confirm_request)
        assert confirmation_attempting_lock.wait(timeout=5)
        assert not confirmation_acquired_lock.wait(timeout=0.2)
        release_forecast.set()
        forecast = forecast_future.result(timeout=5)
        assert confirm_future.result(timeout=5) == 200

    assert forecast["starting_balance"] == "100.0000"
    assert forecast["ending_balance"] == "130.0000"
    with TestClient(app) as client:
        assert (
            client.post("/api/v1/auth/login", json={"master_password": MASTER_PASSWORD}).status_code
            == 200
        )
        after = client.get("/api/v1/forecast?horizon=week").json()
        assert after["starting_balance"] == after["ending_balance"] == "130.0000"
