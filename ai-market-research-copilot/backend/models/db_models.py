from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.core.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    topic = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("Document", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="session", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_kb = Column(Float, nullable=True)
    chunk_count = Column(Integer, default=0)
    indexed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="documents")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id"), nullable=False)
    topic = Column(String(255), nullable=False)
    report_path = Column(String(512), nullable=True)
    executive_summary = Column(Text, nullable=True)
    competitors = Column(Text, nullable=True)       # JSON string
    pricing_insights = Column(Text, nullable=True)  # JSON string
    market_trends = Column(Text, nullable=True)     # JSON string
    swot_analysis = Column(Text, nullable=True)     # JSON string
    status = Column(String(30), default="pending")  # pending, generating, done, failed
    progress = Column(Integer, default=0)
    current_stage = Column(String(80), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("Session", back_populates="reports")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id"), nullable=False)
    role = Column(String(10), nullable=False)   # "user" or "assistant"
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)       # JSON: list of source citations
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="chat_messages")
