from __future__ import annotations

import asyncio
import base64
import logging
from typing import Optional, Protocol


class ImageGenerationClient(Protocol):
    async def generate_image(self, *, prompt: str) -> bytes: ...


class PlaceholderImageClient:
    """Return a lightweight PNG-like byte payload for local development/testing."""

    def __init__(self, *, logger: Optional[logging.Logger] = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    async def generate_image(self, *, prompt: str) -> bytes:
        await asyncio.sleep(0)
        self._logger.debug("Generating placeholder image", extra={"prompt": prompt})
        text = prompt.encode("utf-8")
        encoded = base64.b64encode(text)
        return b"PLACEHOLDER_IMAGE:" + encoded


class GeminiImageClient:
    """Call Gemini 2.5 Flash Image endpoints via google-genai."""

    def __init__(self, *, api_key: str, model: str = "gemini-2.0-flash-exp") -> None:
        self.api_key = api_key
        self.model = model
        try:
            from google import genai  # type: ignore import-not-found
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("GeminiImageClient を利用するには google-genai パッケージが必要です") from exc
        self._client = genai.Client(api_key=api_key)

    async def generate_image(self, *, prompt: str) -> bytes:
        loop = asyncio.get_running_loop()

        def _blocking_call() -> bytes:
            response = self._client.models.generate_image(
                model=self.model,
                prompt=prompt,
            )
            if not response.images:
                raise RuntimeError("Gemini の応答に画像データが含まれていませんでした")
            return response.images[0].data

        return await loop.run_in_executor(None, _blocking_call)
