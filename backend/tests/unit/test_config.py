from sqlalchemy import URL

from app.core.config import Settings


def test_database_url_uses_postgresql_and_keeps_password_out_of_repr() -> None:
    settings = Settings(database_password="private-test-value")

    assert isinstance(settings.database_url, URL)
    assert settings.database_url.drivername == "postgresql+psycopg"
    assert "private-test-value" not in repr(settings.database_password)
