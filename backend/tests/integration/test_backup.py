from copy import deepcopy

from fastapi.testclient import TestClient

from app import APP_VERSION
from app.core.config import Settings
from app.main import create_app
from app.modules.backup.router import MAX_BACKUP_BYTES
from app.modules.backup.schemas import BackupDocument
from app.modules.backup.service import seal_backup, verify_integrity

MASTER_PASSWORD = "correct-master-password"
SETUP = {
    "master_password": MASTER_PASSWORD,
    "base_currency": "RUB",
    "timezone": "Europe/Moscow",
}


def csrf(client: TestClient) -> dict[str, str]:
    return {"X-XSRF-TOKEN": str(client.cookies.get("XSRF-TOKEN"))}


def test_export_preview_and_transactional_restore_on_initialized_database(
    postgres_database_settings: Settings,
) -> None:
    with TestClient(create_app(postgres_database_settings)) as client:
        assert client.get("/api/v1/backup/export").status_code == 401
        assert client.post("/api/v1/setup", json=SETUP).status_code == 201
        headers = csrf(client)
        account = client.post(
            "/api/v1/accounts",
            headers=headers,
            json={"type": "debit", "name": "Main", "initial_balance": "125.5000"},
        ).json()
        category = client.post(
            "/api/v1/categories",
            headers=headers,
            json={"type": "expense", "name": "Food"},
        ).json()

        exported = client.get("/api/v1/backup/export")
        assert exported.status_code == 200
        assert exported.headers["cache-control"] == "no-store"
        document = exported.json()
        assert document["format"] == "hermes-json-backup"
        assert document["schema_version"] == 1
        assert document["app_version"] == "0.1.0-rc.1"
        assert document["data"]["account_movements"][0]["amount"] == "125.5000"
        assert "password" not in exported.text
        assert "sessions" not in document["data"]
        verify_integrity(BackupDocument.model_validate(document))

        preview = client.post("/api/v1/backup/preview", headers=headers, json=document)
        assert preview.status_code == 200
        assert preview.json()["integrity_verified"] is True
        assert preview.json()["counts"]["accounts"] == 1
        assert client.post("/api/v1/backup/preview", json=document).status_code == 403
        oversized = client.post(
            "/api/v1/backup/preview",
            headers={**headers, "Content-Length": str(MAX_BACKUP_BYTES + 1)},
            content=b"{}",
        )
        assert oversized.status_code == 413
        assert oversized.json()["detail"]["code"] == "backup_too_large"

        tampered = deepcopy(document)
        tampered["data"]["accounts"][0]["name"] = "Tampered"
        rejected = client.post("/api/v1/backup/preview", headers=headers, json=tampered)
        assert rejected.status_code == 422
        assert rejected.json()["detail"]["code"] == "invalid_backup"

        assert (
            client.delete(f"/api/v1/accounts/{account['id']}", headers=headers).status_code == 409
        )
        wrong_password = client.post(
            "/api/v1/backup/restore",
            headers=headers,
            json={
                "backup": document,
                "confirmation": "ЗАМЕНИТЬ ВСЕ ДАННЫЕ",
                "master_password": "wrong-master-password",
            },
        )
        assert wrong_password.status_code == 400
        wrong_confirmation = client.post(
            "/api/v1/backup/restore",
            headers=headers,
            json={
                "backup": document,
                "confirmation": "заменить",
                "master_password": MASTER_PASSWORD,
            },
        )
        assert wrong_confirmation.status_code == 400
        assert wrong_confirmation.json()["detail"]["code"] == "confirmation_invalid"

        restored = client.post(
            "/api/v1/backup/restore",
            headers=headers,
            json={
                "backup": document,
                "confirmation": "ЗАМЕНИТЬ ВСЕ ДАННЫЕ",
                "master_password": MASTER_PASSWORD,
            },
        )
        assert restored.status_code == 200
        assert restored.json()["counts"]["categories"] == 1
        assert client.get(f"/api/v1/accounts/{account['id']}").json()["balance"] == "125.5000"
        assert client.get("/api/v1/categories").json()[0]["id"] == category["id"]


def test_restore_complete_backup_into_clean_initialized_target(
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
        ).json()
        category = client.post(
            "/api/v1/categories",
            headers=headers,
            json={"type": "expense", "name": "Food"},
        ).json()
        fund = client.post(
            "/api/v1/funds",
            headers=headers,
            json={"name": "Reserve", "description": None, "allocation_percentage": "10"},
        ).json()
        assert (
            client.post(
                "/api/v1/funds/allocations",
                headers=headers,
                json={
                    "account_id": account["id"],
                    "amount": "20",
                    "occurred_on": "2026-08-12",
                    "description": "Reserve",
                    "allocations": [{"fund_id": fund["id"], "amount": "10"}],
                },
            ).status_code
            == 201
        )
        rule = client.post(
            "/api/v1/scheduling/rules",
            headers=headers,
            json={
                "type": "expense",
                "frequency": "monthly",
                "start_on": "2026-08-12",
                "amount": "5",
                "description": "Food",
                "account_id": account["id"],
                "category_id": category["id"],
            },
        )
        assert rule.status_code == 201
        document = client.get("/api/v1/backup/export").json()

        factory = app.state.session_factory
        with factory.begin() as session:
            from app.modules.backup.schemas import BackupData, BackupIntegrity, SettingsRecord
            from app.modules.backup.service import FORMAT, SCHEMA_VERSION, restore_backup

            settings = document["data"]["settings"]
            empty = BackupData(
                settings=SettingsRecord.model_validate(settings),
                accounts=[],
                categories=[],
                operations=[],
                account_movements=[],
                funds=[],
                fund_events=[],
                fund_movements=[],
                recurring_rules=[],
                expected_occurrences=[],
            )
            blank = BackupDocument(
                format=FORMAT,
                schema_version=SCHEMA_VERSION,
                app_version=APP_VERSION,
                exported_at=document["exported_at"],
                data=empty,
                integrity=BackupIntegrity(digest="0" * 64),
            )
            restore_backup(session, seal_backup(blank))

        restored = client.post(
            "/api/v1/backup/restore",
            headers=headers,
            json={
                "backup": document,
                "confirmation": "ЗАМЕНИТЬ ВСЕ ДАННЫЕ",
                "master_password": MASTER_PASSWORD,
            },
        )
        assert restored.status_code == 200
        assert restored.json()["counts"]["fund_movements"] == 1
        assert restored.json()["counts"]["recurring_rules"] == 1
        assert client.get("/api/v1/funds/summary").json()["total_reserved"] == "10.0000"
        assert len(client.get("/api/v1/scheduling/rules").json()) == 1


def test_failed_restore_rolls_back_existing_data(postgres_database_settings: Settings) -> None:
    with TestClient(create_app(postgres_database_settings)) as client:
        assert client.post("/api/v1/setup", json=SETUP).status_code == 201
        headers = csrf(client)
        account = client.post(
            "/api/v1/accounts",
            headers=headers,
            json={"type": "cash", "name": "Safe", "initial_balance": "10"},
        ).json()
        document = client.get("/api/v1/backup/export").json()
        document["data"]["account_movements"][0]["amount"] = "-10.0000"
        document = seal_backup(BackupDocument.model_validate(document)).model_dump(mode="json")
        rejected = client.post(
            "/api/v1/backup/restore",
            headers=headers,
            json={
                "backup": document,
                "confirmation": "ЗАМЕНИТЬ ВСЕ ДАННЫЕ",
                "master_password": MASTER_PASSWORD,
            },
        )
        assert rejected.status_code == 422
        assert client.get(f"/api/v1/accounts/{account['id']}").json()["balance"] == "10.0000"


def test_restore_reauthentication_is_rate_limited_and_revokes_other_sessions(
    postgres_database_settings: Settings,
) -> None:
    limited = postgres_database_settings.model_copy(update={"login_failure_limit": 2})
    app = create_app(limited)
    with TestClient(app) as first, TestClient(app) as second:
        assert first.post("/api/v1/setup", json=SETUP).status_code == 201
        assert (
            second.post("/api/v1/auth/login", json={"master_password": MASTER_PASSWORD}).status_code
            == 200
        )
        headers = csrf(first)
        document = first.get("/api/v1/backup/export").json()
        payload = {
            "backup": document,
            "confirmation": "ЗАМЕНИТЬ ВСЕ ДАННЫЕ",
            "master_password": "wrong-master-password",
        }
        assert (
            first.post("/api/v1/backup/restore", headers=headers, json=payload).status_code == 400
        )
        limited_response = first.post("/api/v1/backup/restore", headers=headers, json=payload)
        assert limited_response.status_code == 429
        payload["master_password"] = MASTER_PASSWORD
        assert (
            first.post("/api/v1/backup/restore", headers=headers, json=payload).status_code == 429
        )

        factory = app.state.session_factory
        with factory.begin() as session:
            from app.modules.auth.models import LoginThrottle

            throttle = session.get(LoginThrottle, 1)
            assert throttle is not None
            throttle.failed_count = 0
            throttle.window_started_at = None
            throttle.blocked_until = None

        assert (
            first.post("/api/v1/backup/restore", headers=headers, json=payload).status_code == 200
        )
        assert second.get("/api/v1/auth/session").status_code == 401
