from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlmodel import Session, select

from app.agents import get_agent
from app.core.db import get_session
from app.core.dependencies import (
    get_image_generation_client,
    get_llm_client,
    get_storage_service,
)
from app.models import Artifact
from app.services.artifacts import ArtifactService
from app.services.base import StorageService
from app.services.image import ImageGenerationClient
from app.services.llm import LLMClient
from app.services.projects import ProjectService

router = APIRouter(prefix="/tasks", tags=["tasks"])


class KeyframeTaskPayload(BaseModel):
    task_type: str = Field(alias="task_type", default="generate_keyframe")
    project_id: int
    template_code: str = "keyframe_image"
    instructions: str = ""
    created_by: str
    episode: Optional[int] = Field(default=None, ge=1)

    model_config = ConfigDict(populate_by_name=True)


async def _load_previous_summary(
    *,
    session: Session,
    storage: StorageService,
    project_id: int,
    template_code: str,
    episode: Optional[int],
) -> str:
    query = (
        select(Artifact)
        .where(Artifact.project_id == project_id, Artifact.template_code == template_code)
        .order_by(Artifact.version.desc())
    )
    if episode is None:
        query = query.where(Artifact.episode.is_(None))
    else:
        query = query.where(Artifact.episode == episode)

    previous = session.exec(query).first()
    if previous is None:
        return ""
    try:
        data = await storage.load_bytes(previous.storage_path)
        return data.decode("utf-8", errors="ignore")[:1200]
    except FileNotFoundError:
        return ""


@router.post("/generate-keyframe")
async def handle_keyframe_task(
    payload: KeyframeTaskPayload,
    session: Session = Depends(get_session),
    storage: StorageService = Depends(get_storage_service),
    llm: LLMClient = Depends(get_llm_client),
    image_client: ImageGenerationClient = Depends(get_image_generation_client),
):
    if payload.task_type != "generate_keyframe":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported task type")
    if payload.template_code != "keyframe_image":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported template")

    project_service = ProjectService(session=session)
    project = project_service.get_project(payload.project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    summary = await _load_previous_summary(
        session=session,
        storage=storage,
        project_id=payload.project_id,
        template_code="episode_summary",
        episode=payload.episode,
    )

    context = {
        "project_name": project.name,
        "project_description": project.description or "",
        "episode": payload.episode,
        "instructions": payload.instructions,
        "existing_summary": summary,
    }

    agent = get_agent(
        template_code=payload.template_code,
        context=context,
        llm=llm,
        image_client=image_client,
    )
    result = await agent.generate()

    artifact_service = ArtifactService(session=session, storage=storage)
    artifact = await artifact_service.save_binary_artifact(
        project_id=payload.project_id,
        template_code=payload.template_code,
        data=result["content"],
        created_by=payload.created_by,
        episode=payload.episode,
        status="final",
        content_type=result.get("content_type", "image/png"),
    )

    return {
        "artifact_id": artifact.id,
        "storage_path": artifact.storage_path,
        "prompt": result.get("prompt"),
    }
