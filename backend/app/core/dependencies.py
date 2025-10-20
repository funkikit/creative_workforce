from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.core.settings import Settings, get_settings
from app.services.base import StorageService, TaskQueueService, VectorStoreService
from app.services.gcp import CloudTasksQueueService, GCSStorageService, VertexVectorStoreService
from app.services.image import GeminiImageClient, ImageGenerationClient, PlaceholderImageClient
from app.services.llm import LLMClient, OpenAILLMClient, TemplateLLMClient
from app.services.local import InMemoryTaskQueueService, LocalStorageService, LocalVectorStoreService


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
        if not settings.gcs_bucket:
            raise ValueError("GCP 環境では GCS バケットを設定してください")
        return GCSStorageService(
            bucket_name=settings.gcs_bucket,
            base_path=settings.gcs_base_path,
        )
    raise ValueError(f"未対応の env_target 値です: {settings.env_target}")


def _build_vector_store_service(settings: Settings) -> VectorStoreService:
    if settings.env_target == "local":
        return LocalVectorStoreService()
    if settings.env_target == "gcp":
        project_id = settings.vertex_project or settings.gcp_project
        if not project_id:
            raise ValueError("Vertex ベクトルストアには GCP プロジェクト ID の設定が必要です")
        return VertexVectorStoreService(
            project_id=project_id,
            location=settings.vertex_location or settings.gcp_location,
            embedding_model=settings.vertex_embedding_model,
        )
    raise ValueError(f"未対応の env_target 値です: {settings.env_target}")


def _build_task_queue_service(settings: Settings) -> TaskQueueService:
    if settings.env_target == "local":
        return InMemoryTaskQueueService()
    if settings.env_target == "gcp":
        if not settings.cloud_tasks_queue_id or not settings.cloud_tasks_target_url:
            raise ValueError("GCP 環境では Cloud Tasks のキュー ID とターゲット URL を設定してください")
        project_id = settings.cloud_tasks_project or settings.gcp_project
        if not project_id:
            raise ValueError("Cloud Tasks を利用するにはプロジェクト ID の設定が必要です")
        return CloudTasksQueueService(
            project_id=project_id,
            location=settings.cloud_tasks_location or settings.gcp_location,
            queue_id=settings.cloud_tasks_queue_id,
            target_url=settings.cloud_tasks_target_url,
            service_account_email=settings.cloud_tasks_service_account_email,
        )
    raise ValueError(f"未対応の env_target 値です: {settings.env_target}")


def _build_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_provider == "local" or not settings.openai_api_key:
        return TemplateLLMClient(style=settings.llm_output_style)
    return OpenAILLMClient(api_key=settings.openai_api_key, model=settings.llm_model)


def _build_image_generation_client(settings: Settings) -> ImageGenerationClient:
    if settings.image_provider == "placeholder" or not settings.gemini_api_key:
        return PlaceholderImageClient()
    return GeminiImageClient(api_key=settings.gemini_api_key, model=settings.image_model)


@lru_cache(maxsize=1)
def get_storage_service() -> StorageService:
    return _build_storage_service(get_settings())


@lru_cache(maxsize=1)
def get_vector_store_service() -> VectorStoreService:
    return _build_vector_store_service(get_settings())


@lru_cache(maxsize=1)
def get_task_queue_service() -> TaskQueueService:
    return _build_task_queue_service(get_settings())


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    return _build_llm_client(get_settings())


@lru_cache(maxsize=1)
def get_image_generation_client() -> ImageGenerationClient:
    return _build_image_generation_client(get_settings())


def reset_service_providers() -> None:
    """Testing helper to rebuild singletons after environment overrides."""

    get_settings.cache_clear()
    get_storage_service.cache_clear()
    get_vector_store_service.cache_clear()
    get_task_queue_service.cache_clear()
    get_llm_client.cache_clear()
    get_image_generation_client.cache_clear()
