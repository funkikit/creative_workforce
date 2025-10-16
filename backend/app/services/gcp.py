from __future__ import annotations

import asyncio
import json
import logging
import math
from dataclasses import dataclass
from typing import Dict, Optional

from app.services.base import StorageService, TaskQueueService, VectorStoreService
from app.services.local import LocalVectorStoreService, VectorSearchResult


class GCSStorageService(StorageService):
    """Persist bytes in Google Cloud Storage buckets."""

    def __init__(
        self,
        *,
        bucket_name: str,
        base_path: str | None = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.bucket_name = bucket_name
        self.base_path = base_path.strip("/") if base_path else ""
        self._logger = logger or logging.getLogger(__name__)
        self._client = None
        self._bucket = None

    def _get_bucket(self):
        if self._bucket is None:
            try:
                from google.cloud import storage  # type: ignore import-not-found
            except ImportError as exc:  # pragma: no cover - requires optional dependency
                raise RuntimeError(
                    "google-cloud-storage is required for GCSStorageService; install it to continue."
                ) from exc
            self._client = storage.Client()
            self._bucket = self._client.bucket(self.bucket_name)
        return self._bucket

    def _object_name(self, relative_path: str) -> str:
        cleaned = relative_path.strip("/")
        if self.base_path:
            return f"{self.base_path}/{cleaned}"
        return cleaned

    async def save_bytes(self, path: str, data: bytes) -> None:
        object_name = self._object_name(path)
        bucket = self._get_bucket()
        blob = bucket.blob(object_name)

        def _upload() -> None:
            blob.upload_from_string(data)

        self._logger.debug("Uploading blob to GCS", extra={"bucket": self.bucket_name, "object": object_name})
        await asyncio.to_thread(_upload)

    async def load_bytes(self, path: str) -> bytes:
        object_name = self._object_name(path)
        bucket = self._get_bucket()
        blob = bucket.blob(object_name)

        def _download() -> bytes:
            return blob.download_as_bytes()

        self._logger.debug("Downloading blob from GCS", extra={"bucket": self.bucket_name, "object": object_name})
        return await asyncio.to_thread(_download)


class CloudTasksQueueService(TaskQueueService):
    """Publish HTTP tasks to Cloud Tasks."""

    def __init__(
        self,
        *,
        project_id: str,
        location: str,
        queue_id: str,
        target_url: str,
        service_account_email: str | None = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.project_id = project_id
        self.location = location
        self.queue_id = queue_id
        self.target_url = target_url
        self.service_account_email = service_account_email
        self._logger = logger or logging.getLogger(__name__)
        self._client = None

    @property
    def queue_path(self) -> str:
        return f"projects/{self.project_id}/locations/{self.location}/queues/{self.queue_id}"

    def _get_client(self):
        if self._client is None:
            try:
                from google.cloud import tasks_v2  # type: ignore import-not-found
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError(
                    "google-cloud-tasks is required for CloudTasksQueueService; install it to continue."
                ) from exc
            self._client = tasks_v2.CloudTasksClient()
            self._tasks_v2 = tasks_v2
        return self._client

    def enqueue(self, *, task_name: str, payload: Dict[str, object]) -> None:
        client = self._get_client()
        task_body = json.dumps({"task": task_name, "payload": payload}).encode("utf-8")
        http_request = self._tasks_v2.HttpRequest(
            http_method=self._tasks_v2.HttpMethod.POST,
            url=self.target_url,
            headers={"Content-Type": "application/json"},
            body=task_body,
        )
        if self.service_account_email:
            http_request.oidc_token = self._tasks_v2.OidcToken(service_account_email=self.service_account_email)

        task = self._tasks_v2.Task(http_request=http_request)
        self._logger.info(
            "Enqueuing Cloud Task",
            extra={"queue": self.queue_path, "task_name": task_name},
        )
        client.create_task(request={"parent": self.queue_path, "task": task})


@dataclass
class _EmbeddingRecord:
    text: str
    vector: list[float] | None


class VertexVectorStoreService(VectorStoreService):
    """Hybrid vector store with Vertex AI embeddings and substring fallback."""

    def __init__(
        self,
        *,
        project_id: str,
        location: str,
        embedding_model: str = "textembedding-gecko@003",
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.project_id = project_id
        self.location = location
        self.embedding_model_name = embedding_model
        self._logger = logger or logging.getLogger(__name__)
        self._docs: Dict[str, _EmbeddingRecord] = {}
        self._embedding_model = None
        self._embedding_init_attempted = False
        self._fallback = LocalVectorStoreService(logger=logger)

    def _ensure_embedding_model(self):
        if self._embedding_init_attempted:
            return self._embedding_model
        self._embedding_init_attempted = True
        try:
            import vertexai  # type: ignore import-not-found
            from vertexai.preview.language_models import TextEmbeddingModel  # type: ignore import-not-found
        except ImportError as exc:
            self._logger.warning(
                "Vertex AI SDK not available; falling back to substring vector store",
                extra={"error": str(exc)},
            )
            self._embedding_model = None
            return None
        try:
            vertexai.init(project=self.project_id, location=self.location)
            self._embedding_model = TextEmbeddingModel.from_pretrained(self.embedding_model_name)
        except Exception as exc:  # pragma: no cover - requires Vertex setup
            self._logger.warning(
                "Failed to initialise Vertex embeddings; falling back to substring search",
                extra={"error": str(exc)},
            )
            self._embedding_model = None
        return self._embedding_model

    def _embed_text(self, text: str) -> list[float] | None:
        model = self._ensure_embedding_model()
        if model is None:
            return None
        try:
            embedding = model.get_embeddings([text])[0].values  # type: ignore[attr-defined]
            return list(embedding)
        except Exception as exc:  # pragma: no cover - requires Vertex setup
            self._logger.warning("Embedding request failed; falling back to substring search", extra={"error": str(exc)})
            return None

    def add_document(self, *, doc_id: str, text: str) -> None:
        vector = self._embed_text(text)
        self._docs[doc_id] = _EmbeddingRecord(text=text, vector=vector)
        self._fallback.add_document(doc_id=doc_id, text=text)

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query: str, top_k: int = 3) -> list[VectorSearchResult]:
        if not query.strip():
            return []

        query_vector = self._embed_text(query)
        if query_vector is not None:
            scored = []
            for doc_id, record in self._docs.items():
                if record.vector is None:
                    continue
                score = self._cosine_similarity(query_vector, record.vector)
                if score > 0:
                    scored.append(VectorSearchResult(doc_id=doc_id, score=score, text=record.text))
            scored.sort(key=lambda item: item.score, reverse=True)
            if scored:
                return scored[:top_k]

        # fallback to substring search when embeddings are unavailable
        return self._fallback.search(query, top_k=top_k)
