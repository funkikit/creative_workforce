from __future__ import annotations

from typing import Dict, List

from sqlmodel import Session, select

from app.core.templates import EPISODE_TEMPLATES, GLOBAL_TEMPLATES
from app.models import Artifact, Project


class ProjectProgressService:
    """Summarise which artifacts exist or are missing for a project."""

    def __init__(self, *, session: Session) -> None:
        self._session = session

    def project(self, project_id: int) -> Project:
        project = self._session.get(Project, project_id)
        if project is None:
            raise ValueError(f"プロジェクト {project_id} が見つかりません")
        return project

    def summarize(self, project_id: int) -> Dict[str, object]:
        project = self.project(project_id)
        artifacts = list(
            self._session.exec(select(Artifact).where(Artifact.project_id == project_id))
        )

        global_completed = {a.template_code for a in artifacts if a.episode is None}
        global_pending = [code for code in GLOBAL_TEMPLATES if code not in global_completed]

        episodes: List[Dict[str, object]] = []
        for episode in range(1, project.episodes_planned + 1):
            episode_completed = {
                a.template_code for a in artifacts if a.episode == episode
            }
            episode_pending = [code for code in EPISODE_TEMPLATES if code not in episode_completed]
            episodes.append(
                {
                    "episode": episode,
                    "completed": sorted(episode_completed),
                    "pending": episode_pending,
                }
            )

        return {
            "project_id": project_id,
            "global": {"completed": sorted(global_completed), "pending": global_pending},
            "episodes": episodes,
        }
