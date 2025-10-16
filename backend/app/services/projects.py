from __future__ import annotations

import logging
from typing import Optional

from sqlmodel import Session, select

from app.models import Project


class ProjectService:
    """Manage project lifecycle and queries."""

    def __init__(self, *, session: Session, logger: Optional[logging.Logger] = None) -> None:
        self._session = session
        self._logger = logger or logging.getLogger(__name__)

    def create_project(
        self, *, name: str, description: str | None = None, episodes_planned: int = 1
    ) -> Project:
        project = Project(name=name, description=description, episodes_planned=episodes_planned)
        self._session.add(project)
        self._session.commit()
        self._session.refresh(project)
        self._logger.info("Project created", extra={"project_id": project.id, "name": name})
        return project

    def list_projects(self) -> list[Project]:
        return list(self._session.exec(select(Project)))

    def get_project(self, project_id: int) -> Project | None:
        return self._session.get(Project, project_id)
