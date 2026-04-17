from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Session ──────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    topic: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    topic: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Document ─────────────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size_kb: Optional[float]
    chunk_count: int
    indexed: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Research ─────────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    session_id: str
    topic: str


class CompetitorInfo(BaseModel):
    name: str
    description: str
    strengths: List[str] = []
    weaknesses: List[str] = []
    market_position: str = ""


class PricingInsight(BaseModel):
    segment: str
    price_range: str
    key_players: List[str] = []
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
    executive_summary: Optional[str]
    competitors: Optional[List[CompetitorInfo]]
    pricing_insights: Optional[List[PricingInsight]]
    market_trends: Optional[List[MarketTrend]]
    swot_analysis: Optional[SwotAnalysis]
    report_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str


class SourceCitation(BaseModel):
    filename: str
    chunk_index: int
    excerpt: str
    relevance_score: float


class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str
    sources: List[SourceCitation] = []


class ChatHistoryResponse(BaseModel):
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    session_id: str
    filename: str
    file_type: str
    chunk_count: int
    message: str


# ── Generic ──────────────────────────────────────────────────────────────────

class StatusResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
