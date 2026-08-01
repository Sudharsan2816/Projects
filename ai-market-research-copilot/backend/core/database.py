from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend.models import db_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_report_job_columns()


def _migrate_report_job_columns() -> None:
    """Add report-job fields to existing SQLite databases without destructive migration."""
    inspector = inspect(engine)
    if "reports" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("reports")}
    additions = {
        "progress": "INTEGER DEFAULT 0",
        "current_stage": "VARCHAR(80)",
        "error_message": "TEXT",
        "updated_at": "DATETIME",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE reports ADD COLUMN {name} {definition}"))
