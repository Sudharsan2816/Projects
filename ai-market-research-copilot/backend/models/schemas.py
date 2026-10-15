from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# ── Session ──────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    topic: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    topic: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Document ─────────────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size_kb: Optional[float]
    chunk_count: int
    indexed: bool
    brief: Optional[str] = None
    brief_status: str = "pending"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Research ─────────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    topic: str = Field(min_length=3, max_length=255)
    document_ids: Optional[List[int]] = Field(default=None, max_length=50)


class CompetitorInfo(BaseModel):
    name: str
    description: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    market_position: str = ""


class PricingInsight(BaseModel):
    segment: str
    price_range: str
    key_players: List[str] = Field(default_factory=list)
    notes: str = ""


class MarketTrend(BaseModel):
    trend: str
    description: str
    impact: str = ""
    timeframe: str = ""


class SwotAnalysis(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]


class ReportResponse(BaseModel):
    report_id: int
    session_id: str
    topic: str
    status: str
    progress: int = 0
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    executive_summary: Optional[str]
    competitors: Optional[List[CompetitorInfo]]
    pricing_insights: Optional[List[PricingInsight]]
    market_trends: Optional[List[MarketTrend]]
    swot_analysis: Optional[SwotAnalysis]
    report_path: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=10000)


class SourceCitation(BaseModel):
    filename: str
    chunk_index: int
    excerpt: str
    relevance_score: float


class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str
    sources: List[SourceCitation] = Field(default_factory=list)
    answer_mode: Literal[
        "documents", "general_market_knowledge", "report_irrelevant", "out_of_scope"
    ] = "documents"


class ChatHistoryResponse(BaseModel):
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]]
    answer_mode: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    session_id: str
    document_id: int
    filename: str
    file_type: str
    chunk_count: int
    brief: Optional[str] = None
    brief_status: Literal["pending", "ready", "unavailable"] = "pending"
    message: str


class DocumentBriefResponse(BaseModel):
    document_id: int
    brief: Optional[str] = None
    brief_status: Literal["pending", "ready", "unavailable"]


# ── Generic ──────────────────────────────────────────────────────────────────

class StatusResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
