from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session, select

from app.agents import get_agent
from app.core.db import get_session
from app.core.templates import EPISODE_TEMPLATES, GLOBAL_TEMPLATES, validate_template_code
from app.models import Artifact, ArtifactRead, ProjectCreate, ProjectRead
from app.services.artifacts import ArtifactService
from app.services.base import StorageService, TaskQueueService
from app.services.progress import ProjectProgressService
from app.services.projects import ProjectService
from app.core.dependencies import (
    get_image_generation_client,
    get_llm_client,
    get_storage_service,
    get_task_queue_service,
)
from app.services.image import ImageGenerationClient
from app.services.llm import LLMClient


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=List[ProjectRead])
def list_projects(session: Session = Depends(get_session)) -> List[ProjectRead]:
    projects = ProjectService(session=session).list_projects()
    return [ProjectRead.model_validate(project) for project in projects]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, session: Session = Depends(get_session)) -> ProjectRead:
    project = ProjectService(session=session).create_project(
        name=payload.name,
        description=payload.description,
        episodes_planned=payload.episodes_planned,
    )
    return ProjectRead.model_validate(project)


@router.get("/{project_id}/artifacts", response_model=List[ArtifactRead])
def list_project_artifacts(project_id: int, session: Session = Depends(get_session)) -> List[ArtifactRead]:
    project = ProjectService(session=session).get_project(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    artifacts = session.exec(
        select(Artifact)
        .where(Artifact.project_id == project_id)
        .order_by(Artifact.created_at.desc())
    ).all()
    return [ArtifactRead.model_validate(artifact) for artifact in artifacts]


class ArtifactCreatePayload(BaseModel):
    template_code: str
    content: str
    created_by: str
    episode: Optional[int] = Field(default=None, ge=1)
    status: str = "draft"
    content_type: str = "text/markdown"


class AgentGenerationRequest(BaseModel):
    instructions: str = ""
    created_by: str
    episode: Optional[int] = Field(default=None, ge=1)


class GeneratedArtifactResponse(BaseModel):
    artifact: ArtifactRead
    metadata: Dict[str, Any]


class GenerationQueuedResponse(BaseModel):
    status: str = "queued"
    queue: str
    template_code: str


class ArtifactContentResponse(BaseModel):
    artifact: ArtifactRead
    content: Optional[str]
    content_type: str
    is_binary: bool = False


class CompletionSummary(BaseModel):
    completed: List[str]
    pending: List[str]


class EpisodeSummary(BaseModel):
    episode: int
    completed: List[str]
    pending: List[str]


class ProjectProgressResponse(BaseModel):
    project_id: int
    global_summary: CompletionSummary = Field(alias="global")
    episodes: List[EpisodeSummary]

    model_config = ConfigDict(populate_by_name=True)


@router.post(
    "/{project_id}/artifacts",
    response_model=ArtifactRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_artifact(
    project_id: int,
    payload: ArtifactCreatePayload,
    session: Session = Depends(get_session),
    storage: StorageService = Depends(get_storage_service),
) -> ArtifactRead:
    project_service = ProjectService(session=session)
    project = project_service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    try:
        validate_template_code(payload.template_code)
    except ValueError as exc:  # pragma: no cover - input validation path
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    _validate_template_episode(
        template_code=payload.template_code,
        project=project,
        episode=payload.episode,
    )

    artifact = await ArtifactService(session=session, storage=storage).save_text_artifact(
        project_id=project_id,
        template_code=payload.template_code,
        content=payload.content,
        created_by=payload.created_by,
        episode=payload.episode,
        status=payload.status,
        content_type=payload.content_type,
    )
    return ArtifactRead.model_validate(artifact)


def _validate_template_episode(
    *,
    template_code: str,
    project,  # Project model
    episode: Optional[int],
) -> None:
    if template_code in EPISODE_TEMPLATES:
        if episode is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Episode is required for episodic templates",
            )
        if episode > project.episodes_planned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Episode exceeds planned count",
            )
    else:
        if episode is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Episode must be omitted for global templates",
            )


async def _load_previous_artifact_summary(
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


@router.post(
    "/{project_id}/artifacts/{template_code}/generate",
    response_model=Union[GeneratedArtifactResponse, GenerationQueuedResponse],
)
async def generate_project_artifact(
    project_id: int,
    template_code: str,
    payload: AgentGenerationRequest,
    session: Session = Depends(get_session),
    storage: StorageService = Depends(get_storage_service),
    llm: LLMClient = Depends(get_llm_client),
    image_client: ImageGenerationClient = Depends(get_image_generation_client),
    task_queue: TaskQueueService = Depends(get_task_queue_service),
) -> Union[GeneratedArtifactResponse, GenerationQueuedResponse]:
    try:
        validate_template_code(template_code)
    except ValueError as exc:  # pragma: no cover - validation guard
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    project_service = ProjectService(session=session)
    project = project_service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    _validate_template_episode(
        template_code=template_code, project=project, episode=payload.episode
    )

    existing_summary = await _load_previous_artifact_summary(
        session=session,
        storage=storage,
        project_id=project_id,
        template_code=template_code,
        episode=payload.episode,
    )

    context = {
        "project_name": project.name,
        "project_description": project.description or "",
        "episode": payload.episode,
        "instructions": payload.instructions,
        "existing_summary": existing_summary,
    }

    if template_code == "keyframe_image":
        task_queue.enqueue(
            task_name="generate_keyframe",
            payload={
                "task_type": "generate_keyframe",
                "project_id": project_id,
                "template_code": template_code,
                "episode": payload.episode,
                "instructions": payload.instructions,
                "created_by": payload.created_by,
            },
        )
        queued = GenerationQueuedResponse(queue="keyframe", template_code=template_code)
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=queued.model_dump(),
        )

    agent = get_agent(
        template_code=template_code,
        context=context,
        llm=llm,
        image_client=image_client,
    )
    result = await agent.generate()

    artifact_service = ArtifactService(session=session, storage=storage)
    artifact = await artifact_service.save_text_artifact(
        project_id=project_id,
        template_code=template_code,
        content=result["content"],
        created_by=payload.created_by,
        episode=payload.episode,
    )

    return GeneratedArtifactResponse(
        artifact=ArtifactRead.model_validate(artifact),
        metadata=result.get("metadata", {}),
    )


@router.get(
    "/{project_id}/artifacts/{artifact_id}", response_model=ArtifactContentResponse
)
async def get_artifact_content(
    project_id: int,
    artifact_id: int,
    session: Session = Depends(get_session),
    storage: StorageService = Depends(get_storage_service),
) -> ArtifactContentResponse:
    artifact = session.get(Artifact, artifact_id)
    if artifact is None or artifact.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    try:
        data = await storage.load_bytes(artifact.storage_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact file missing") from exc

    try:
        binary_hint = artifact.storage_path.lower().endswith(
            (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bin")
        )
        if binary_hint:
            raise UnicodeDecodeError("binary", b"", 0, 1, "binary file")
        content = data.decode("utf-8")
        return ArtifactContentResponse(
            artifact=ArtifactRead.model_validate(artifact),
            content=content,
            content_type="text/plain",
            is_binary=False,
        )
    except UnicodeDecodeError:
        encoded = base64.b64encode(data).decode("ascii")
        return ArtifactContentResponse(
            artifact=ArtifactRead.model_validate(artifact),
            content=encoded,
            content_type="application/octet-stream",
            is_binary=True,
        )


@router.get("/{project_id}/progress", response_model=ProjectProgressResponse)
def project_progress(
    project_id: int, session: Session = Depends(get_session)
) -> ProjectProgressResponse:
    project_service = ProjectService(session=session)
    project = project_service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    summary = ProjectProgressService(session=session).summarize(project_id)
    return ProjectProgressResponse.model_validate(summary)
