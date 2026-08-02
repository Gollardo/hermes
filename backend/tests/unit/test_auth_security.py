from typing import get_args

from fastapi.params import Depends

from app.core.database import DatabaseSession
from app.modules.auth.schemas import SetupRequest
from app.modules.auth.security import hash_password, hash_token, verify_password


def test_password_is_stored_as_argon2id_hash() -> None:
    password = "a-long-master-password"

    password_hash = hash_password(password)

    assert password_hash.startswith("$argon2id$")
    assert password not in password_hash
    assert verify_password(password_hash, password)
    assert not verify_password(password_hash, "incorrect-password")


def test_opaque_tokens_are_stored_as_one_way_digests() -> None:
    token = "browser-only-session-token"

    digest = hash_token(token)

    assert token not in digest
    assert len(digest) == 64


def test_setup_normalizes_currency_and_validates_timezone() -> None:
    request = SetupRequest(
        master_password="a-long-master-password",
        base_currency=" rub ",
        timezone="Europe/Moscow",
    )

    assert request.base_currency == "RUB"
    assert request.timezone == "Europe/Moscow"


def test_database_transaction_finishes_before_response_is_sent() -> None:
    dependency = next(
        annotation for annotation in get_args(DatabaseSession) if isinstance(annotation, Depends)
    )

    assert dependency.scope == "function"
