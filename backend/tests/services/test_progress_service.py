from pathlib import Path

import pytest

from app.core import db
from app.models import Artifact, Project
from app.services.progress import ProjectProgressService


@pytest.fixture
def sqlite_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'progress.db'}")
    db.reset_engine()
    db.init_db()
    yield tmp_path
    db.reset_engine()


def test_summarize_returns_missing_templates(sqlite_env: Path) -> None:
    with db.session() as session:
        project = Project(name="Story", episodes_planned=2)
        session.add(project)
        session.commit()
        session.refresh(project)

        session.add(
            Artifact(
                project_id=project.id,
                template_code="overall_spec",
                storage_path="projects/1/overall_spec/v001.md",
                created_by="tester",
            )
        )
        session.add(
            Artifact(
                project_id=project.id,
                template_code="episode_summary",
                episode=1,
                storage_path="projects/1/episodes/01/episode_summary/v001.md",
                created_by="tester",
            )
        )
        session.commit()

        progress = ProjectProgressService(session=session).summarize(project.id)

    assert progress["global"]["completed"] == ["overall_spec"]
    assert "character_design" in progress["global"]["pending"]
    episode_one = next(item for item in progress["episodes"] if item["episode"] == 1)
    episode_two = next(item for item in progress["episodes"] if item["episode"] == 2)

    assert episode_one["completed"] == ["episode_summary"]
    assert "episode_script" in episode_one["pending"]
    assert set(episode_two["completed"]) == set()
    assert "episode_summary" in episode_two["pending"]
