from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.templates import EPISODE_TEMPLATES, GLOBAL_TEMPLATES, validate_template_code
from app.models import Artifact, ArtifactRead, ProjectCreate, ProjectRead
from app.services.artifacts import ArtifactService
from app.services.base import StorageService
from app.services.progress import ProjectProgressService
from app.services.projects import ProjectService
from app.core.dependencies import get_storage_service


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

    if payload.template_code in EPISODE_TEMPLATES:
        if payload.episode is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Episode is required for episodic templates",
            )
        if payload.episode > project.episodes_planned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Episode exceeds planned count",
            )
    else:
        if payload.episode is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Episode must be omitted for global templates",
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
