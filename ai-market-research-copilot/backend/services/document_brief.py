from typing import Any

from backend.services.llm import generate

MAX_BRIEF_CONTEXT_CHARS = 14_000
MAX_CHUNK_EXCERPT_CHARS = 1_800

BRIEF_SYSTEM_PROMPT = """You are a careful market-research source analyst.
Use only the supplied document excerpts. Do not add outside knowledge, current facts, or
unsupported conclusions. If the source does not contain an item, say so plainly."""


def _sample_context(chunks: list[dict[str, Any]]) -> str:
    """Select excerpts across the whole document while keeping the prompt bounded."""
    if not chunks:
        return ""

    sample_count = min(len(chunks), 10)
    if sample_count == 1:
        indexes = [0]
    else:
        indexes = sorted(
            {
                round(position * (len(chunks) - 1) / (sample_count - 1))
                for position in range(sample_count)
            }
        )

    excerpts: list[str] = []
    remaining = MAX_BRIEF_CONTEXT_CHARS
    per_excerpt = min(MAX_CHUNK_EXCERPT_CHARS, MAX_BRIEF_CONTEXT_CHARS // len(indexes))
    for index in indexes:
        chunk = chunks[index]
        text = " ".join(str(chunk.get("text", "")).split())
        if not text or remaining <= 0:
            continue
        page = chunk.get("page", "unknown")
        excerpt = text[: min(per_excerpt, remaining)]
        excerpts.append(f"[Page/section {page}]\n{excerpt}")
        remaining -= len(excerpt)

    return "\n\n".join(excerpts)


def build_document_brief(filename: str, chunks: list[dict[str, Any]]) -> str:
    """Generate a concise, document-grounded briefing for an indexed source."""
    context = _sample_context(chunks)
    if not context:
        raise ValueError("The document contains no text that can be summarized")

    prompt = f"""Create a concise briefing for the uploaded source \"{filename}\".

Return plain text using exactly these headings:
Overview
Key findings
Important figures
Research gaps

Under Overview, write 2-3 sentences describing the source and its focus.
Under Key findings, provide 3-5 short bullet points.
Under Important figures, list only figures explicitly present in the source; write
\"No material figures found in the sampled text.\" if none are present.
Under Research gaps, list 1-3 important questions the source does not answer.
Keep the complete briefing under 260 words and never invent a claim.

DOCUMENT EXCERPTS
{context}
"""
    brief = generate(prompt, BRIEF_SYSTEM_PROMPT).strip()
    if len(brief) < 40:
        raise ValueError("The briefing provider returned an incomplete response")
    return brief
