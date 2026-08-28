import base64
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.modules.backup.errors import (
    BackupAuthenticationFailed,
    InvalidHermesFile,
    InvalidKdfParameters,
    UnsupportedHermesVersion,
)
from app.modules.backup.hermes_v1 import HermesV1Reader, HermesV1Writer, parse_backup_envelope
from app.modules.backup.schemas import BackupData, BackupDocument, BackupIntegrity, SettingsRecord
from app.modules.backup.service import seal_backup

PASSWORD = "correct-master-password"


def legacy_backup() -> BackupDocument:
    now = datetime.now(UTC)
    return seal_backup(
        BackupDocument(
            format="hermes-json-backup",
            schema_version=1,
            app_version="1.0.0",
            exported_at=now,
            data=BackupData(
                settings=SettingsRecord(
                    base_currency="RUB",
                    timezone="Europe/Moscow",
                    default_account_id=None,
                    fund_allocation_mode="manual",
                    base_currency_locked_at=None,
                    created_at=now,
                    updated_at=now,
                ),
                accounts=[],
                categories=[],
                operations=[],
                account_movements=[],
                funds=[],
                fund_events=[],
                fund_movements=[],
                recurring_rules=[],
                expected_occurrences=[],
            ),
            integrity=BackupIntegrity(digest="0" * 64),
        )
    )


def test_hermes_v1_round_trip_contains_no_plaintext_financial_data() -> None:
    source = legacy_backup()
    encrypted = HermesV1Writer().write(PASSWORD, source)

    serialized = encrypted.model_dump_json()
    assert encrypted.format == "hermes"
    assert encrypted.version == 1
    assert encrypted.kdf.algorithm == "argon2id"
    assert encrypted.key_encryption.algorithm == "xchacha20-poly1305-ietf"
    assert encrypted.payload_encryption.algorithm == "xchacha20-poly1305-ietf"
    assert "Europe/Moscow" not in serialized
    assert "base_currency" not in serialized

    restored = HermesV1Reader().read(PASSWORD, encrypted)
    assert restored.data == source.data
    assert restored.exported_at == source.exported_at


def test_hermes_v1_uses_fresh_salt_dek_and_nonces() -> None:
    source = legacy_backup()
    first = HermesV1Writer().write(PASSWORD, source)
    second = HermesV1Writer().write(PASSWORD, source)

    assert first.kdf.salt != second.kdf.salt
    assert first.key_encryption.nonce != first.payload_encryption.nonce
    assert first.key_encryption.nonce != second.key_encryption.nonce
    assert first.key_encryption.encrypted_data_key != second.key_encryption.encrypted_data_key
    assert first.payload_encryption.ciphertext != second.payload_encryption.ciphertext


@pytest.mark.parametrize("tamper", ["password", "wrapped_key", "payload", "metadata"])
def test_hermes_v1_returns_one_authentication_error(tamper: str) -> None:
    encrypted = HermesV1Writer().write(PASSWORD, legacy_backup())
    password = PASSWORD
    if tamper == "password":
        password = "wrong-master-password"
    elif tamper == "wrapped_key":
        encrypted.key_encryption.encrypted_data_key = _flip(
            encrypted.key_encryption.encrypted_data_key
        )
    elif tamper == "payload":
        encrypted.payload_encryption.ciphertext = _flip(encrypted.payload_encryption.ciphertext)
    else:
        encrypted.created_at = encrypted.created_at.replace(year=2025)

    with pytest.raises(BackupAuthenticationFailed, match="Incorrect password or corrupted backup"):
        HermesV1Reader().read(password, encrypted)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("memory_cost", 65_535),
        ("memory_cost", 262_145),
        ("time_cost", 2),
        ("time_cost", 7),
        ("parallelism", 0),
        ("parallelism", 9),
        ("hash_len", 16),
        ("argon2_version", 18),
    ],
)
def test_unsafe_kdf_parameters_are_rejected_before_argon2(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: int,
) -> None:
    encrypted = HermesV1Writer().write(PASSWORD, legacy_backup())
    setattr(encrypted.kdf, field, value)

    def unexpected_argon2(**kwargs: object) -> bytes:
        raise AssertionError("Argon2 must not run for untrusted parameters")

    monkeypatch.setattr("app.modules.backup.hermes_v1.hash_secret_raw", unexpected_argon2)
    with pytest.raises(InvalidKdfParameters):
        HermesV1Reader().read(PASSWORD, encrypted)


@pytest.mark.parametrize(
    ("field", "value", "error_type"),
    [
        ("salt", base64.b64encode(b"s" * 15).decode("ascii"), InvalidKdfParameters),
        ("key_nonce", base64.b64encode(b"n" * 23).decode("ascii"), InvalidHermesFile),
        ("payload_nonce", base64.b64encode(b"n" * 25).decode("ascii"), InvalidHermesFile),
        ("encrypted_data_key", base64.b64encode(b"k" * 47).decode("ascii"), InvalidHermesFile),
        ("ciphertext", base64.b64encode(b"c" * 15).decode("ascii"), InvalidHermesFile),
    ],
)
def test_unsafe_encoded_lengths_are_rejected_before_argon2(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
    error_type: type[ValueError],
) -> None:
    encrypted = HermesV1Writer().write(PASSWORD, legacy_backup())
    if field == "salt":
        encrypted.kdf.salt = value
    elif field == "key_nonce":
        encrypted.key_encryption.nonce = value
    elif field == "payload_nonce":
        encrypted.payload_encryption.nonce = value
    elif field == "encrypted_data_key":
        encrypted.key_encryption.encrypted_data_key = value
    else:
        encrypted.payload_encryption.ciphertext = value

    def unexpected_argon2(**kwargs: object) -> bytes:
        raise AssertionError("Argon2 must not run for unsafe encoded lengths")

    monkeypatch.setattr("app.modules.backup.hermes_v1.hash_secret_raw", unexpected_argon2)
    with pytest.raises(error_type):
        HermesV1Reader().read(PASSWORD, encrypted)


def test_oversized_ciphertext_is_rejected_before_argon2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    encrypted = HermesV1Writer().write(PASSWORD, legacy_backup())
    encrypted.payload_encryption.ciphertext = base64.b64encode(b"c" * 17).decode("ascii")
    monkeypatch.setattr("app.modules.backup.hermes_v1.MAX_PAYLOAD_CIPHERTEXT_BYTES", 16)

    def unexpected_argon2(**kwargs: object) -> bytes:
        raise AssertionError("Argon2 must not run for oversized ciphertext")

    monkeypatch.setattr("app.modules.backup.hermes_v1.hash_secret_raw", unexpected_argon2)
    with pytest.raises(InvalidHermesFile):
        HermesV1Reader().read(PASSWORD, encrypted)


def test_unknown_hermes_version_is_rejected_explicitly() -> None:
    raw = HermesV1Writer().write(PASSWORD, legacy_backup()).model_dump(mode="json")
    raw["version"] = 2

    with pytest.raises(UnsupportedHermesVersion, match="Unsupported Hermes backup version"):
        parse_backup_envelope(raw)


def test_malformed_legacy_backup_is_not_misclassified_as_hermes() -> None:
    raw = legacy_backup().model_dump(mode="json")
    del raw["data"]

    with pytest.raises(ValidationError):
        parse_backup_envelope(raw)


def _flip(value: str) -> str:
    decoded = bytearray(base64.b64decode(value))
    decoded[-1] ^= 1
    return base64.b64encode(decoded).decode("ascii")
