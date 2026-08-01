"""Prompt templates."""

SYSTEM_PROMPT = """Answer ONLY from provided enterprise context.
Never invent information.
If insufficient data exists, say so.
Never reveal unauthorized information.
Summarize concisely and cite source labels from context when useful."""


def build_grounded_prompt(query: str, contexts: list[dict]) -> str:
    context_text = "\n\n".join(
        f"[{idx + 1}] source={item.get('source')} permission={item.get('permission')}\n{item.get('content')}"
        for idx, item in enumerate(contexts)
    )
    return f"{SYSTEM_PROMPT}\n\nEnterprise context:\n{context_text}\n\nUser question: {query}\nAnswer:"
