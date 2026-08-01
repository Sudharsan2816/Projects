from typing import Dict, List

from backend.core.logging import get_logger

logger = get_logger(__name__)


def search_market_data(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search the web for real market data to ground LLM responses.
    Returns a list of {title, url, body} dicts.
    Falls back to empty list if search fails.
    """
    try:
        from ddgs import DDGS
        results = list(DDGS().text(query, max_results=max_results))
        logger.info("Web search '%s' returned %s results", query[:60], len(results))
        return results
    except Exception as e:
        logger.warning(f"Web search failed ({e}), proceeding without grounding")
        return []


def build_web_context(topic: str, section: str) -> str:
    """
    Fetch real web data for a given market research section and format it
    as a grounding context block for the LLM prompt.
    """
    queries = {
        "summary":     f"{topic} market size revenue CAGR growth rate 2024",
        "competitors": f"{topic} top companies market share key players 2024",
        "pricing":     f"{topic} pricing price range segments 2024",
        "trends":      f"{topic} market trends growth drivers 2024 2025",
        "swot":        f"{topic} market challenges threats opportunities analysis",
    }
    query = queries.get(section, f"{topic} market research {section} 2024")
    results = search_market_data(query, max_results=5)

    if not results:
        return ""

    lines = ["=== REAL WEB DATA (use these facts, do not fabricate alternatives) ==="]
    for i, r in enumerate(results, 1):
        lines.append(f"[Source {i}] {r.get('title','')}")
        lines.append(r.get('body', '')[:300])
        lines.append("")

    return "\n".join(lines)
