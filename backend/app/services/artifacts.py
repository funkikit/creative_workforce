from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from sqlmodel import Session, select

from app.models import Artifact
from app.services.base import StorageService


class ArtifactService:
    """Handle artifact persistence and versioning while delegating blob storage."""

    _CONTENT_TYPE_EXTENSIONS = {
        "text/markdown": ".md",
        "text/plain": ".txt",
        "application/json": ".json",
        "application/octet-stream": ".bin",
        "image/png": ".png",
    }

    def __init__(
        self,
        *,
        session: Session,
        storage: StorageService,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._session = session
        self._storage = storage
        self._logger = logger or logging.getLogger(__name__)

    async def save_text_artifact(
        self,
        *,
        project_id: int,
        template_code: str,
        content: str,
        created_by: str,
        episode: Optional[int] = None,
        status: str = "draft",
        content_type: str = "text/markdown",
    ) -> Artifact:
        version = self._next_version(project_id=project_id, template_code=template_code, episode=episode)
        extension = self._CONTENT_TYPE_EXTENSIONS.get(content_type, ".txt")
        relative_path = self._build_storage_path(
            project_id=project_id,
            template_code=template_code,
            version=version,
            extension=extension,
            episode=episode,
        )

        self._logger.debug(
            "Saving artifact",
            extra={
                "project_id": project_id,
                "template_code": template_code,
                "episode": episode,
                "version": version,
                "path": str(relative_path),
            },
        )

        await self._storage.save_bytes(str(relative_path), content.encode("utf-8"))

        artifact = Artifact(
            project_id=project_id,
            template_code=template_code,
            episode=episode,
            version=version,
            status=status,
            storage_path=str(relative_path),
            created_by=created_by,
        )
        self._session.add(artifact)
        self._session.commit()
        self._session.refresh(artifact)
        return artifact

    async def save_binary_artifact(
        self,
        *,
        project_id: int,
        template_code: str,
        data: bytes,
        created_by: str,
        episode: Optional[int] = None,
        status: str = "final",
        content_type: str = "application/octet-stream",
    ) -> Artifact:
        version = self._next_version(project_id=project_id, template_code=template_code, episode=episode)
        extension = self._CONTENT_TYPE_EXTENSIONS.get(content_type, ".bin")
        relative_path = self._build_storage_path(
            project_id=project_id,
            template_code=template_code,
            version=version,
            extension=extension,
            episode=episode,
        )

        self._logger.debug(
            "Saving binary artifact",
            extra={
                "project_id": project_id,
                "template_code": template_code,
                "episode": episode,
                "version": version,
                "path": str(relative_path),
            },
        )

        await self._storage.save_bytes(str(relative_path), data)

        artifact = Artifact(
            project_id=project_id,
            template_code=template_code,
            episode=episode,
            version=version,
            status=status,
            storage_path=str(relative_path),
            created_by=created_by,
        )
        self._session.add(artifact)
        self._session.commit()
        self._session.refresh(artifact)
        return artifact

    def _next_version(self, *, project_id: int, template_code: str, episode: Optional[int]) -> int:
        query = (
            select(Artifact.version)
            .where(Artifact.project_id == project_id, Artifact.template_code == template_code)
            .order_by(Artifact.version.desc())
        )
        if episode is None:
            query = query.where(Artifact.episode.is_(None))
        else:
            query = query.where(Artifact.episode == episode)

        current = self._session.exec(query).first()
        return 1 if current is None else current + 1

    def _build_storage_path(
        self,
        *,
        project_id: int,
        template_code: str,
        version: int,
        extension: str,
        episode: Optional[int],
    ) -> Path:
        if episode is None:
            base = Path(f"projects/{project_id}/{template_code}")
        else:
            base = Path(f"projects/{project_id}/episodes/{episode:02d}/{template_code}")
        filename = f"v{version:03d}{extension}"
        return base / filename
