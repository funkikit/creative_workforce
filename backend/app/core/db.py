from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.core.settings import get_settings

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_engine(
            settings.database_url,
            echo=settings.sqlalchemy_echo,
            connect_args=connect_args,
        )
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None
    get_settings.cache_clear()


def init_db() -> None:
    SQLModel.metadata.create_all(get_engine())


@contextmanager
def session() -> Iterator[Session]:
    with Session(get_engine()) as db_session:
        yield db_session


def get_session() -> Iterator[Session]:
    with session() as db_session:
        yield db_session
