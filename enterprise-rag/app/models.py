"""Database models."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

AuthBase = declarative_base()
EnterpriseBase = declarative_base()
AuditBase = declarative_base()


auth_engine = create_engine(settings.auth_db_url, connect_args={"check_same_thread": False})
enterprise_engine = create_engine(settings.enterprise_db_url, connect_args={"check_same_thread": False})
audit_engine = create_engine(settings.audit_db_url, connect_args={"check_same_thread": False})

AuthSessionLocal = sessionmaker(bind=auth_engine, autoflush=False, autocommit=False)
EnterpriseSessionLocal = sessionmaker(bind=enterprise_engine, autoflush=False, autocommit=False)
AuditSessionLocal = sessionmaker(bind=audit_engine, autoflush=False, autocommit=False)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(AuthBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(40), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class EmployeeRecord(EnterpriseBase):
    __tablename__ = "employee_records"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(30), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    department = Column(String(80), nullable=False)
    title = Column(String(120), nullable=False)
    manager = Column(String(120), nullable=False)
    salary_band = Column(String(20), nullable=False)
    performance_rating = Column(String(20), nullable=False)


class FinanceReport(EnterpriseBase):
    __tablename__ = "finance_reports"

    id = Column(Integer, primary_key=True, index=True)
    quarter = Column(String(20), nullable=False)
    business_unit = Column(String(80), nullable=False)
    revenue = Column(Float, nullable=False)
    expenses = Column(Float, nullable=False)
    risk_notes = Column(Text, nullable=False)


class AuditLog(AuditBase):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(80), nullable=True)
    role = Column(String(40), nullable=True)
    query = Column(Text, nullable=False)
    retrieval_sources = Column(Text, nullable=False)
    response_status = Column(String(80), nullable=False)
    security_flags = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


def init_databases() -> None:
    AuthBase.metadata.create_all(bind=auth_engine)
    EnterpriseBase.metadata.create_all(bind=enterprise_engine)
    AuditBase.metadata.create_all(bind=audit_engine)
