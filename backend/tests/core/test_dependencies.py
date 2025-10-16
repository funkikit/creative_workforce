from pathlib import Path

import pytest

from app.core import dependencies
from app.services.local import InMemoryTaskQueueService, LocalStorageService, LocalVectorStoreService


@pytest.fixture(autouse=True)
def reset_providers() -> None:
    dependencies.reset_service_providers()
    yield
    dependencies.reset_service_providers()


def test_get_storage_service_uses_local_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_STORAGE_ROOT", str(tmp_path))
    dependencies.reset_service_providers()
    storage = dependencies.get_storage_service()
    assert isinstance(storage, LocalStorageService)
    assert storage.root == tmp_path


def test_get_vector_store_service_returns_local_impl() -> None:
    vector_store = dependencies.get_vector_store_service()
    assert isinstance(vector_store, LocalVectorStoreService)


def test_get_task_queue_service_returns_local_impl() -> None:
    task_queue = dependencies.get_task_queue_service()
    assert isinstance(task_queue, InMemoryTaskQueueService)
