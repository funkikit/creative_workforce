from pathlib import Path

import pytest

from app.core import db
from app.services.projects import ProjectService


@pytest.fixture
def sqlite_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'projects.db'}")
    db.reset_engine()
    db.init_db()
    yield tmp_path
    db.reset_engine()


def test_create_project(sqlite_env: Path) -> None:
    with db.session() as session:
        service = ProjectService(session=session)
        project = service.create_project(name="Test Project", description="desc")

        projects = service.list_projects()

    assert project.id is not None
    assert len(projects) == 1
    assert projects[0].name == "Test Project"
