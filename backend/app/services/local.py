from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass(slots=True)
class TaskJob:
    task_name: str
    payload: Dict[str, object]


class InMemoryTaskQueueService:
    """Simple in-memory queue used for local development and tests."""

    def __init__(self, *, logger: Optional[logging.Logger] = None) -> None:
        self._queue: deque[TaskJob] = deque()
        self._logger = logger or logging.getLogger(__name__)

    def enqueue(self, *, task_name: str, payload: Dict[str, object]) -> None:
        self._queue.append(TaskJob(task_name=task_name, payload=payload))
        self._logger.debug(
            "Enqueued task",
            extra={"task_name": task_name, "queue_depth": len(self._queue)},
        )

    def pop(self) -> Optional[TaskJob]:
        if not self._queue:
            self._logger.warning("Attempted to pop from empty task queue")
            return None
        job = self._queue.popleft()
        self._logger.debug(
            "Dequeued task",
            extra={"task_name": job.task_name, "remaining": len(self._queue)},
        )
        return job


@dataclass(slots=True)
class VectorSearchResult:
    doc_id: str
    score: float
    text: str


class LocalVectorStoreService:
    """Naive vector store backed by substring matching. Suitable for unit tests only."""

    def __init__(self, *, logger: Optional[logging.Logger] = None) -> None:
        self._docs: Dict[str, str] = {}
        self._logger = logger or logging.getLogger(__name__)

    def add_document(self, *, doc_id: str, text: str) -> None:
        if not doc_id:
            raise ValueError("doc_id must be provided")
        self._docs[doc_id] = text
        self._logger.debug(
            "Document added to local vector store",
            extra={"doc_id": doc_id, "text_length": len(text)},
        )

    def search(self, query: str, top_k: int = 3) -> list[VectorSearchResult]:
        if not query.strip():
            self._logger.warning("Vector store search received empty query")
            return []
        scored = []
        for doc_id, text in self._docs.items():
            score = text.lower().count(query.lower())
            if score > 0:
                scored.append(VectorSearchResult(doc_id=doc_id, score=float(score), text=text))
        scored.sort(key=lambda item: item.score, reverse=True)
        if not scored:
            self._logger.info("Vector store search returned no matches", extra={"query": query})
        return scored[:top_k]


class LocalStorageService:
    """Persist bytes on the local filesystem."""

    def __init__(self, root: Path, *, logger: Optional[logging.Logger] = None) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._resolved_root = self.root.resolve()
        self._logger = logger or logging.getLogger(__name__)

    def _resolve(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        try:
            candidate.relative_to(self._resolved_root)
        except ValueError as exc:  # pragma: no cover - defensive, but easy to trigger
            raise ValueError(f"Path {relative_path!r} escapes local storage root") from exc
        return candidate

    async def save_bytes(self, relative_path: str, data: bytes) -> None:
        path = self._resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, path.write_bytes, data)
        except OSError as exc:
            self._logger.error("Failed to write file", extra={"path": str(path), "error": str(exc)})
            raise

    async def load_bytes(self, relative_path: str) -> bytes:
        path = self._resolve(relative_path)
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(None, path.read_bytes)
        except FileNotFoundError as exc:
            self._logger.warning("File not found in local storage", extra={"path": str(path)})
            raise
        except OSError as exc:
            self._logger.error("Failed to read file", extra={"path": str(path), "error": str(exc)})
            raise
