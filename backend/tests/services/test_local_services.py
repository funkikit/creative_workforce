from pathlib import Path

import pytest

from app.services.local import (
    InMemoryTaskQueueService,
    LocalStorageService,
    LocalVectorStoreService,
)


@pytest.fixture()
def tmp_storage(tmp_path: Path) -> LocalStorageService:
    return LocalStorageService(root=tmp_path)


@pytest.mark.asyncio
async def test_local_storage_save_and_load(tmp_storage: LocalStorageService) -> None:
    await tmp_storage.save_bytes("artifacts/sample.txt", b"hello")
    data = await tmp_storage.load_bytes("artifacts/sample.txt")
    assert data == b"hello"


def test_vector_store_add_and_search() -> None:
    store = LocalVectorStoreService()
    store.add_document(doc_id="doc-1", text="creative story about space")
    store.add_document(doc_id="doc-2", text="cooking recipe")

    results = store.search("story", top_k=1)
    assert len(results) == 1
    assert results[0].doc_id == "doc-1"


def test_task_queue_enqueue_and_pop() -> None:
    queue = InMemoryTaskQueueService()
    queue.enqueue(task_name="generate", payload={"artifact_id": 1})
    job = queue.pop()
    assert job is not None
    assert job.task_name == "generate"
    assert job.payload == {"artifact_id": 1}


def test_task_queue_empty_when_no_jobs() -> None:
    queue = InMemoryTaskQueueService()
    assert queue.pop() is None
