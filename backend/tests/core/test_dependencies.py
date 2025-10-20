from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from app.core import dependencies
from app.services.gcp import CloudTasksQueueService, GCSStorageService, VertexVectorStoreService
from app.services.image import PlaceholderImageClient
from app.services.llm import OpenAILLMClient, TemplateLLMClient
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


def test_llm_and_image_clients_are_local_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    dependencies.reset_service_providers()
    llm = dependencies.get_llm_client()
    image_client = dependencies.get_image_generation_client()

    assert isinstance(llm, TemplateLLMClient)
    assert isinstance(image_client, PlaceholderImageClient)


def test_llm_client_returns_openai_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    fake_client = SimpleNamespace()
    fake_openai_module = SimpleNamespace(AsyncOpenAI=lambda api_key: fake_client)
    monkeypatch.setitem(sys.modules, "openai", fake_openai_module)
    dependencies.reset_service_providers()

    llm = dependencies.get_llm_client()

    assert isinstance(llm, OpenAILLMClient)


def test_gcp_dependencies_return_gcp_services(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV_TARGET", "gcp")
    monkeypatch.setenv("GCP_PROJECT", "demo-project")
    monkeypatch.setenv("GCS_BUCKET", "demo-bucket")
    monkeypatch.setenv("CLOUD_TASKS_QUEUE_ID", "default")
    monkeypatch.setenv("CLOUD_TASKS_TARGET_URL", "https://example.com/task")
    monkeypatch.setenv("VERTEX_EMBEDDING_MODEL", "textembedding-gecko@003")
    dependencies.reset_service_providers()

    storage = dependencies.get_storage_service()
    vector_store = dependencies.get_vector_store_service()
    task_queue = dependencies.get_task_queue_service()

    assert isinstance(storage, GCSStorageService)
    assert isinstance(vector_store, VertexVectorStoreService)
    assert isinstance(task_queue, CloudTasksQueueService)
