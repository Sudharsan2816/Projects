import json
from typing import Optional

from .rag import rag_query
from .llm import generate, generate_json
from .vector_store import FAISSVectorStore
from backend.core.logging import get_logger

logger = get_logger(__name__)

SYSTEM = "You are a senior market research analyst with 15+ years of experience in competitive intelligence, pricing strategy, and market trend analysis."


def _has_documents(session_id: str) -> bool:
    store = FAISSVectorStore(session_id)
    return store.total_vectors() > 0


def _query(session_id: str, q: str) -> str:
    if _has_documents(session_id):
        answer, _ = rag_query(session_id, q, system_prompt=SYSTEM)
        return answer
    else:
        return generate(q, SYSTEM)


# ── Executive Summary ─────────────────────────────────────────────────────────

def generate_executive_summary(session_id: str, topic: str) -> str:
    q = f"""Write a concise executive summary (3-4 paragraphs) for a market research report on:
Topic: {topic}

Include:
- Market overview and size estimate
- Key dynamics and growth drivers
- Critical challenges
- Strategic outlook"""
    return _query(session_id, q)


# ── Competitors ───────────────────────────────────────────────────────────────

def extract_competitors(session_id: str, topic: str) -> list:
    q = f"""Identify and analyze the top 5 competitors in the {topic} market.

Return a JSON array. Each item must have:
{{
  "name": "Company Name",
  "description": "Brief company description",
  "strengths": ["strength1", "strength2"],
  "weaknesses": ["weakness1", "weakness2"],
  "market_position": "Leader/Challenger/Niche/Follower"
}}

Return ONLY the JSON array."""

    if _has_documents(session_id):
        raw, _ = rag_query(session_id, q, system_prompt=SYSTEM)
    else:
        raw = generate(q, SYSTEM)

    # Try to parse JSON from the response
    try:
        # Find JSON array in response
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception as e:
        logger.error(f"Competitor JSON parse failed: {e}")

    # Fallback: return structured placeholder
    return [
        {
            "name": "Data unavailable",
            "description": "Could not extract competitor data. Please upload relevant documents.",
            "strengths": [],
            "weaknesses": [],
            "market_position": "Unknown",
        }
    ]


# ── Pricing Insights ──────────────────────────────────────────────────────────

def extract_pricing_insights(session_id: str, topic: str) -> list:
    q = f"""Analyze pricing strategies and price points in the {topic} market.

Return a JSON array. Each item must have:
{{
  "segment": "Premium/Mid-range/Budget/etc",
  "price_range": "e.g. ₹200-500 per unit",
  "key_players": ["Brand A", "Brand B"],
  "notes": "Key insight about this pricing segment"
}}

Return ONLY the JSON array."""

    if _has_documents(session_id):
        raw, _ = rag_query(session_id, q, system_prompt=SYSTEM)
    else:
        raw = generate(q, SYSTEM)

    try:
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception as e:
        logger.error(f"Pricing JSON parse failed: {e}")

    return [{"segment": "Unavailable", "price_range": "N/A", "key_players": [], "notes": "Upload relevant documents for pricing analysis."}]


# ── Market Trends ─────────────────────────────────────────────────────────────

def extract_market_trends(session_id: str, topic: str) -> list:
    q = f"""Identify the top 5 market trends shaping the {topic} market.

Return a JSON array. Each item must have:
{{
  "trend": "Short trend name",
  "description": "Detailed explanation of the trend",
  "impact": "High/Medium/Low",
  "timeframe": "Short-term/Medium-term/Long-term"
}}

Return ONLY the JSON array."""

    if _has_documents(session_id):
        raw, _ = rag_query(session_id, q, system_prompt=SYSTEM)
    else:
        raw = generate(q, SYSTEM)

    try:
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception as e:
        logger.error(f"Trends JSON parse failed: {e}")

    return [{"trend": "Unavailable", "description": "Upload documents for trend analysis.", "impact": "N/A", "timeframe": "N/A"}]


# ── SWOT Analysis ─────────────────────────────────────────────────────────────

def generate_swot(session_id: str, topic: str) -> dict:
    q = f"""Perform a SWOT analysis for a new entrant in the {topic} market.

Return a JSON object with exactly this structure:
{{
  "strengths": ["point1", "point2", "point3", "point4"],
  "weaknesses": ["point1", "point2", "point3", "point4"],
  "opportunities": ["point1", "point2", "point3", "point4"],
  "threats": ["point1", "point2", "point3", "point4"]
}}

Return ONLY the JSON object."""

    if _has_documents(session_id):
        raw, _ = rag_query(session_id, q, system_prompt=SYSTEM)
    else:
        raw = generate(q, SYSTEM)

    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception as e:
        logger.error(f"SWOT JSON parse failed: {e}")

    return {
        "strengths": ["Data unavailable"],
        "weaknesses": ["Data unavailable"],
        "opportunities": ["Data unavailable"],
        "threats": ["Data unavailable"],
    }


# ── Full Report ───────────────────────────────────────────────────────────────

def generate_full_report(session_id: str, topic: str) -> dict:
    """Orchestrate all research sections and return combined dict."""
    logger.info(f"[{session_id}] Generating full report for topic: {topic}")

    summary = generate_executive_summary(session_id, topic)
    competitors = extract_competitors(session_id, topic)
    pricing = extract_pricing_insights(session_id, topic)
    trends = extract_market_trends(session_id, topic)
    swot = generate_swot(session_id, topic)

    return {
        "executive_summary": summary,
        "competitors": competitors,
        "pricing_insights": pricing,
        "market_trends": trends,
        "swot_analysis": swot,
    }
