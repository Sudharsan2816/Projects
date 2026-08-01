"""LLM client with OpenAI support and local fallback."""

from __future__ import annotations

from app.config import settings
from app.llm.prompts import build_grounded_prompt


class LLMClient:
    def __init__(self) -> None:
        self.client = None
        if settings.openai_api_key:
            try:
                from openai import OpenAI

                self.client = OpenAI(api_key=settings.openai_api_key)
            except Exception:
                self.client = None

    def generate(self, query: str, contexts: list[dict]) -> str:
        if self.client:
            prompt = build_grounded_prompt(query, contexts)
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a secure enterprise RAG assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            return response.choices[0].message.content or ""
        return self._local_grounded_answer(query, contexts)

    def _local_grounded_answer(self, query: str, contexts: list[dict]) -> str:
        if not contexts:
            return "Insufficient authorized enterprise context is available to answer this question."
        lines = ["Based on authorized enterprise context:"]
        for idx, item in enumerate(contexts[:5], start=1):
            content = " ".join(item.get("content", "").split())
            if len(content) > 450:
                content = content[:447] + "..."
            lines.append(f"{idx}. {content} (source: {item.get('source')})")
        return "\n".join(lines)


llm_client = LLMClient()
