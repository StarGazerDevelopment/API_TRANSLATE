from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        _apply_sqlite_compat_migrations()


def _apply_sqlite_compat_migrations() -> None:
    endpoint_columns = {
        "summary": "TEXT DEFAULT ''",
        "endpoint_type": "VARCHAR(50) DEFAULT 'chat'",
        "compatibility_json": "TEXT DEFAULT '[\"openai\"]'",
        "model_name": "VARCHAR(255)",
    }
    settings_columns = {
        "endpoint_style": "VARCHAR(50) DEFAULT 'openai'",
    }

    with engine.begin() as connection:
        result = connection.execute(text("PRAGMA table_info(endpoints)"))
        existing_columns = {row[1] for row in result}
        for column_name, column_ddl in endpoint_columns.items():
            if column_name not in existing_columns:
                connection.execute(text(f"ALTER TABLE endpoints ADD COLUMN {column_name} {column_ddl}"))

        settings_result = connection.execute(text("PRAGMA table_info(settings)"))
        existing_setting_columns = {row[1] for row in settings_result}
        for column_name, column_ddl in settings_columns.items():
            if column_name not in existing_setting_columns:
                connection.execute(text(f"ALTER TABLE settings ADD COLUMN {column_name} {column_ddl}"))
