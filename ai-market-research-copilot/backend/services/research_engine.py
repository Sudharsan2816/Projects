import json
import re
from typing import Optional

from .rag import rag_query
from .llm import generate, generate_json
from .vector_store import FAISSVectorStore
from .web_search import build_web_context
from backend.core.logging import get_logger

logger = get_logger(__name__)

SYSTEM = "You are a senior market research analyst with 15+ years of experience in competitive intelligence, pricing strategy, and market trend analysis."

# Anti-hallucination guardrail appended to every prompt when no documents are uploaded
_GUARDRAIL = """
STRICT RULES — you must follow these exactly:
1. Only state specific figures (market size, CAGR, revenue) if you are highly confident they are accurate. If uncertain, express as a RANGE (e.g., "USD 100M–500M" or "CAGR of 6%–12%").
2. Never invent company names, brand names, or market share percentages.
3. If real web data is provided above, use those figures exactly. Do not contradict or ignore them.
4. For any figure you are less than 90% confident about, write "approximately" or "estimated" before it.
5. Do not fill in placeholder text like [Current Year] or [Projected Year] — use actual years.
"""


def _parse_json_safe(raw: str, kind: str = "array"):
    """Extract and parse a JSON array or object from raw LLM output, tolerating minor formatting."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw.strip())
    if kind == "array":
        start, end = raw.find("["), raw.rfind("]") + 1
    else:
        start, end = raw.find("{"), raw.rfind("}") + 1
    if start < 0 or end <= start:
        return None
    candidate = raw[start:end]
    candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _has_documents(session_id: str) -> bool:
    store = FAISSVectorStore(session_id)
    return store.total_vectors() > 0


def _query(session_id: str, prompt: str, web_context: str = "") -> str:
    """Run prompt through RAG (if docs exist) or LLM, with optional web grounding."""
    has_docs = _has_documents(session_id)
    full_prompt = f"{web_context}\n\n{prompt}" if web_context else prompt
    system = SYSTEM if has_docs else SYSTEM + _GUARDRAIL

    if has_docs:
        answer, _ = rag_query(session_id, full_prompt, system_prompt=system)
    else:
        answer = generate(full_prompt, system)
    return answer


def _llm_json(session_id: str, prompt: str, kind: str = "array",
              web_context: str = "", retries: int = 2):
    """Run prompt with grounding + guardrails, parse JSON, retry on failure."""
    has_docs = _has_documents(session_id)
    system = SYSTEM if has_docs else SYSTEM + _GUARDRAIL
    full_prompt = f"{web_context}\n\n{prompt}" if web_context else prompt

    for attempt in range(retries + 1):
        if has_docs:
            raw, _ = rag_query(session_id, full_prompt, system_prompt=system)
        else:
            raw = generate(full_prompt, system)
        result = _parse_json_safe(raw, kind)
        if result:
            return result
        if attempt < retries:
            logger.warning(f"[{session_id}] JSON parse attempt {attempt+1} failed, retrying")
    return None


# ── Executive Summary ─────────────────────────────────────────────────────────

def generate_executive_summary(session_id: str, topic: str) -> str:
    web_ctx = build_web_context(topic, "summary")
    q = f"""Write a concise executive summary (3-4 paragraphs) for a market research report on:
Topic: {topic}

Include:
- Market overview and size estimate (use ranges if exact figures are uncertain, cite "according to industry reports")
- Key dynamics and growth drivers
- Critical challenges
- Strategic outlook

Do not use placeholder text like [Current Year]. Use specific years (2024, 2025, etc.)."""
    return _query(session_id, q, web_ctx)


# ── Competitors ───────────────────────────────────────────────────────────────

def extract_competitors(session_id: str, topic: str) -> list:
    web_ctx = build_web_context(topic, "competitors")
    q = f"""Identify and analyze the top 5 real, verified competitors in the {topic} market.

Only include companies that actually exist and operate in this market.

Return a JSON array. Each item must have:
{{
  "name": "Actual Company Name",
  "description": "Brief verified description",
  "strengths": ["strength1", "strength2"],
  "weaknesses": ["weakness1", "weakness2"],
  "market_position": "Leader/Challenger/Niche/Follower"
}}

Return ONLY the JSON array."""

    result = _llm_json(session_id, q, "array", web_ctx)
    if result:
        return result
    logger.error(f"[{session_id}] Competitor JSON parse failed after retries")
    return [{"name": "Data unavailable", "description": "Upload relevant documents for competitor analysis.", "strengths": [], "weaknesses": [], "market_position": "Unknown"}]


# ── Pricing Insights ──────────────────────────────────────────────────────────

def extract_pricing_insights(session_id: str, topic: str) -> list:
    web_ctx = build_web_context(topic, "pricing")
    q = f"""Analyze pricing strategies and price points in the {topic} market.

Use Rs. instead of the rupee symbol. Only state price ranges you are confident about.
If uncertain about exact prices, use ranges (e.g., "Rs. 50-150 per bar").

Return a JSON array. Each item must have:
{{
  "segment": "Premium/Mid-range/Budget/etc",
  "price_range": "e.g. Rs. 80-120 per bar",
  "key_players": ["Brand A", "Brand B"],
  "notes": "Key insight about this pricing segment"
}}

Return ONLY the JSON array."""

    result = _llm_json(session_id, q, "array", web_ctx)
    if result:
        return result
    logger.error(f"[{session_id}] Pricing JSON parse failed after retries")
    return [{"segment": "Unavailable", "price_range": "N/A", "key_players": [], "notes": "Upload relevant documents for pricing analysis."}]


# ── Market Trends ─────────────────────────────────────────────────────────────

def extract_market_trends(session_id: str, topic: str) -> list:
    web_ctx = build_web_context(topic, "trends")
    q = f"""Identify the top 5 market trends shaping the {topic} market in 2024-2025.

Base your answer on real, verifiable trends. Do not invent trends.

Return a JSON array. Each item must have:
{{
  "trend": "Short trend name",
  "description": "Detailed explanation with real context",
  "impact": "High/Medium/Low",
  "timeframe": "Short-term/Medium-term/Long-term"
}}

Return ONLY the JSON array."""

    result = _llm_json(session_id, q, "array", web_ctx)
    if result:
        return result
    logger.error(f"[{session_id}] Trends JSON parse failed after retries")
    return [{"trend": "Unavailable", "description": "Upload documents for trend analysis.", "impact": "N/A", "timeframe": "N/A"}]


# ── SWOT Analysis ─────────────────────────────────────────────────────────────

def generate_swot(session_id: str, topic: str) -> dict:
    web_ctx = build_web_context(topic, "swot")
    q = f"""Perform a SWOT analysis for a new entrant in the {topic} market.

Base each point on real market conditions. Do not fabricate statistics.

Return a JSON object with exactly this structure:
{{
  "strengths": ["point1", "point2", "point3", "point4"],
  "weaknesses": ["point1", "point2", "point3", "point4"],
  "opportunities": ["point1", "point2", "point3", "point4"],
  "threats": ["point1", "point2", "point3", "point4"]
}}

Return ONLY the JSON object."""

    result = _llm_json(session_id, q, "object", web_ctx)
    if result:
        return result
    logger.error(f"[{session_id}] SWOT JSON parse failed after retries")
    return {"strengths": ["Data unavailable"], "weaknesses": ["Data unavailable"], "opportunities": ["Data unavailable"], "threats": ["Data unavailable"]}


# ── Full Report ───────────────────────────────────────────────────────────────

def generate_full_report(session_id: str, topic: str) -> dict:
    """Orchestrate all research sections and return combined dict."""
    logger.info(f"[{session_id}] Generating full report for topic: {topic}")
    has_docs = _has_documents(session_id)
    data_source = "uploaded_documents" if has_docs else "web_search+llm"
    logger.info(f"[{session_id}] Data source: {data_source}")

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
        "data_source": data_source,
    }
