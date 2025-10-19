from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol


class LLMClient(Protocol):
    async def generate_text(self, *, prompt: str, temperature: float = 0.3) -> str: ...


@dataclass
class TemplateLLMClient:
    """Deterministic LLM stub for local development and tests."""

    style: str = "markdown"

    async def generate_text(self, *, prompt: str, temperature: float = 0.3) -> str:
        await asyncio.sleep(0)
        header = f"# {self.style} のサンプル出力"
        body = prompt.strip()
        return f"{header}\n\n{body}\n\n- 使用温度: {temperature:.1f}"


class OpenAILLMClient:
    """Thin wrapper around the OpenAI responses API."""

    def __init__(self, *, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        try:
            from openai import AsyncOpenAI  # type: ignore import-not-found
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("OpenAILLMClient を利用するには openai パッケージが必要です") from exc
        self._client = AsyncOpenAI(api_key=api_key)

    async def generate_text(self, *, prompt: str, temperature: float = 0.3) -> str:
        response = await self._client.responses.create(
            model=self.model,
            input=prompt,
            temperature=temperature,
        )
        return response.output_text
