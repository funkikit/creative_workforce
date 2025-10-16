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


@pytest.mark.asyncio
async def test_local_storage_missing_file_raises(tmp_storage: LocalStorageService) -> None:
    with pytest.raises(FileNotFoundError):
        await tmp_storage.load_bytes("missing.bin")


@pytest.mark.asyncio
async def test_local_storage_rejects_escape_paths(tmp_storage: LocalStorageService) -> None:
    with pytest.raises(ValueError):
        await tmp_storage.save_bytes("../outside.txt", b"nope")


def test_vector_store_add_and_search() -> None:
    store = LocalVectorStoreService()
    store.add_document(doc_id="doc-1", text="creative story about space")
    store.add_document(doc_id="doc-2", text="cooking recipe")

    results = store.search("story", top_k=1)
    assert len(results) == 1
    assert results[0].doc_id == "doc-1"


def test_vector_store_empty_query_returns_no_results() -> None:
    store = LocalVectorStoreService()
    store.add_document(doc_id="doc-1", text="creative story about space")
    assert store.search("") == []


def test_vector_store_empty_query_logs_warning(caplog: pytest.LogCaptureFixture) -> None:
    store = LocalVectorStoreService()
    with caplog.at_level("WARNING"):
        store.search("")
    assert any("empty query" in message for message in caplog.messages)


def test_vector_store_requires_doc_id() -> None:
    store = LocalVectorStoreService()
    with pytest.raises(ValueError):
        store.add_document(doc_id="", text="oops")


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


def test_task_queue_logs_when_empty(caplog: pytest.LogCaptureFixture) -> None:
    queue = InMemoryTaskQueueService()
    with caplog.at_level("WARNING"):
        assert queue.pop() is None
    assert any("empty task queue" in message for message in caplog.messages)
