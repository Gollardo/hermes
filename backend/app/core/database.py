from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings


class Base(DeclarativeBase):
    """Shared metadata registry; domain modules own their mapped models."""


def create_database_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_pre_ping=True,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """Provide a transaction boundary for a single application operation."""
    with factory.begin() as session:
        yield session


def get_database_session(request: Request) -> Iterator[Session]:
    """Commit one successful HTTP use case or roll it back on failure."""
    factory = cast(sessionmaker[Session], request.app.state.session_factory)
    with factory.begin() as session:
        yield session


# Function scope closes and commits the transaction before FastAPI sends the
# response. This keeps a successful HTTP status and any issued cookies atomic
# with the database operation they represent.
DatabaseSession = Annotated[
    Session,
    Depends(get_database_session, scope="function"),
]
