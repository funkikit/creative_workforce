from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageService(Protocol):
    async def save_bytes(self, path: str, data: bytes) -> None: ...

    async def load_bytes(self, path: str) -> bytes: ...


class VectorStoreService(ABC):
    @abstractmethod
    def add_document(self, *, doc_id: str, text: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, top_k: int = 3):
        raise NotImplementedError


class TaskQueueService(ABC):
    @abstractmethod
    def enqueue(self, *, task_name: str, payload: dict) -> None:
        raise NotImplementedError
