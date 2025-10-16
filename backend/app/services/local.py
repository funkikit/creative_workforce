from __future__ import annotations

import asyncio
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

    def __init__(self) -> None:
        self._queue: deque[TaskJob] = deque()

    def enqueue(self, *, task_name: str, payload: Dict[str, object]) -> None:
        self._queue.append(TaskJob(task_name=task_name, payload=payload))

    def pop(self) -> Optional[TaskJob]:
        if not self._queue:
            return None
        return self._queue.popleft()


@dataclass(slots=True)
class VectorSearchResult:
    doc_id: str
    score: float
    text: str


class LocalVectorStoreService:
    """Naive vector store backed by substring matching. Suitable for unit tests only."""

    def __init__(self) -> None:
        self._docs: Dict[str, str] = {}

    def add_document(self, *, doc_id: str, text: str) -> None:
        self._docs[doc_id] = text

    def search(self, query: str, top_k: int = 3) -> list[VectorSearchResult]:
        scored = []
        for doc_id, text in self._docs.items():
            score = text.lower().count(query.lower())
            if score > 0:
                scored.append(VectorSearchResult(doc_id=doc_id, score=float(score), text=text))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]


class LocalStorageService:
    """Persist bytes on the local filesystem."""

    def __init__(self, root: Path) -> None:
        self.root = root

    async def save_bytes(self, relative_path: str, data: bytes) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, path.write_bytes, data)

    async def load_bytes(self, relative_path: str) -> bytes:
        path = self.root / relative_path
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, path.read_bytes)
