import asyncio
from typing import Dict

import pytest

from app.services.gcp import CloudTasksQueueService, GCSStorageService, VertexVectorStoreService


class _StubBlob:
    def __init__(self) -> None:
        self.saved: bytes | None = None

    def upload_from_string(self, data: bytes) -> None:
        self.saved = data

    def download_as_bytes(self) -> bytes:
        if self.saved is None:
            raise FileNotFoundError("No data stored")
        return self.saved


class _StubBucket:
    def __init__(self) -> None:
        self._objects: Dict[str, _StubBlob] = {}

    def blob(self, name: str) -> _StubBlob:
        return self._objects.setdefault(name, _StubBlob())


@pytest.mark.asyncio
async def test_gcs_storage_service_upload_and_download() -> None:
    service = GCSStorageService(bucket_name="unused", base_path="artifacts")
    bucket = _StubBucket()
    service._get_bucket = lambda: bucket  # type: ignore[assignment]

    await service.save_bytes("project/file.txt", b"payload")
    data = await service.load_bytes("project/file.txt")

    assert data == b"payload"


def test_cloud_tasks_queue_service_enqueues() -> None:
    captured = {}

    class StubClient:
        def __init__(self) -> None:
            self.requests = []

        def create_task(self, request):
            captured.update(request)

    service = CloudTasksQueueService(
        project_id="demo",
        location="asia-northeast1",
        queue_id="default",
        target_url="https://example.com/tasks",
    )
    stub_client = StubClient()
    service._get_client = lambda: stub_client  # type: ignore[assignment]
    service._tasks_v2 = type(
        "TasksModule",
        (),
        {
            "HttpMethod": type("HttpMethod", (), {"POST": 1}),
            "HttpRequest": lambda **kw: kw,
            "OidcToken": lambda **kw: kw,
            "Task": lambda **kw: kw,
        },
    )

    service.enqueue(task_name="generate", payload={"project_id": 1})

    assert captured["parent"].endswith("queues/default")
    assert captured["task"]["http_request"]["url"] == "https://example.com/tasks"


def test_vertex_vector_store_fallback_search(monkeypatch: pytest.MonkeyPatch) -> None:
    store = VertexVectorStoreService(project_id="demo", location="asia-northeast1")
    monkeypatch.setattr(store, "_embed_text", lambda text: None)

    store.add_document(doc_id="doc-1", text="space opera pilot")
    results = store.search("space")

    assert len(results) == 1
    assert results[0].doc_id == "doc-1"
