"""SQLite engine, session management, and database initialization."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.runtime_paths import application_directory


DATABASE_PATH = application_directory() / "cafepos.db"
engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def enable_foreign_keys(dbapi_connection: object, _connection_record: object) -> None:
    """Enable SQLite foreign-key enforcement for every connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def initialize_database() -> None:
    """Create the SQLite database and all known tables when needed."""
    import app.models  # noqa: F401

    Base.metadata.create_all(engine)
    _add_missing_discount_columns()


def _add_missing_discount_columns() -> None:
    """Add discount history columns to databases created before Module 4.5."""
    with engine.begin() as connection:
        existing_columns = {
            column[1]
            for column in connection.exec_driver_sql("PRAGMA table_info(orders)")
        }
        missing_columns = {
            "discount_scope": "TEXT",
            "discount_menu_item_id": "INTEGER",
        }
        for name, column_type in missing_columns.items():
            if name not in existing_columns:
                connection.execute(text(f"ALTER TABLE orders ADD COLUMN {name} {column_type}"))


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transaction that commits on success and rolls back on error."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
