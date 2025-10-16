from abc import ABC, abstractmethod
from typing import Protocol


class StorageService(Protocol):
    def save_bytes(self, path: str, data: bytes) -> None: ...

    def load_bytes(self, path: str) -> bytes: ...


class VectorStoreService(ABC):
    @abstractmethod
    def add_document(self, *, doc_id: str, text: str) -> None:
        raise NotImplementedError


class TaskQueueService(ABC):
    @abstractmethod
    def enqueue(self, *, task_name: str, payload: dict) -> None:
        raise NotImplementedError
