"""Pydantic request and response schemas."""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=128)
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: str


class QueryRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)


class QueryResponse(BaseModel):
    answer: str
    intent: str
    sources: list[str]
    status: str
    security_flags: list[str]


class UploadResponse(BaseModel):
    filename: str
    source_type: str
    status: str
    indexed_chunks: int = 0


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    username: str | None
    role: str | None
    query: str
    retrieval_sources: str
    response_status: str
    security_flags: str
    created_at: str
