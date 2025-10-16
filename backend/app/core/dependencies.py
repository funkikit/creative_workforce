from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.core.settings import Settings, get_settings
from app.services.base import StorageService, TaskQueueService, VectorStoreService
from app.services.local import (
    InMemoryTaskQueueService,
    LocalStorageService,
    LocalVectorStoreService,
)


def _resolve_local_storage_root(settings: Settings) -> Path:
    root = Path(settings.local_storage_root).expanduser()
    if not root.is_absolute():
        # Keep storage rooted within the backend directory when a relative path is provided.
        backend_root = Path(__file__).resolve().parents[2]
        root = (backend_root / root).resolve()
    return root


def _build_storage_service(settings: Settings) -> StorageService:
    if settings.env_target == "local":
        return LocalStorageService(root=_resolve_local_storage_root(settings))
    if settings.env_target == "gcp":
        raise NotImplementedError("GCP storage service wiring not implemented yet")
    raise ValueError(f"Unsupported env_target: {settings.env_target}")


def _build_vector_store_service(settings: Settings) -> VectorStoreService:
    if settings.env_target == "local":
        return LocalVectorStoreService()
    if settings.env_target == "gcp":
        raise NotImplementedError("GCP vector store service wiring not implemented yet")
    raise ValueError(f"Unsupported env_target: {settings.env_target}")


def _build_task_queue_service(settings: Settings) -> TaskQueueService:
    if settings.env_target == "local":
        return InMemoryTaskQueueService()
    if settings.env_target == "gcp":
        raise NotImplementedError("GCP task queue service wiring not implemented yet")
    raise ValueError(f"Unsupported env_target: {settings.env_target}")


@lru_cache(maxsize=1)
def get_storage_service() -> StorageService:
    return _build_storage_service(get_settings())


@lru_cache(maxsize=1)
def get_vector_store_service() -> VectorStoreService:
    return _build_vector_store_service(get_settings())


@lru_cache(maxsize=1)
def get_task_queue_service() -> TaskQueueService:
    return _build_task_queue_service(get_settings())


def reset_service_providers() -> None:
    """Testing helper to rebuild singletons after environment overrides."""

    get_settings.cache_clear()
    get_storage_service.cache_clear()
    get_vector_store_service.cache_clear()
    get_task_queue_service.cache_clear()
