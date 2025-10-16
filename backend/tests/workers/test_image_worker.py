import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core import db, dependencies
from app.main import create_application
from app.models import Project
from app.services.artifacts import ArtifactService
from app.services.local import LocalStorageService


@pytest.fixture
def worker_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    storage_root = tmp_path / "storage"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'worker.db'}")
    monkeypatch.setenv("LOCAL_STORAGE_ROOT", str(storage_root))
    db.reset_engine()
    db.init_db()
    dependencies.reset_service_providers()

    with db.session() as session:
        project = Project(name="Worker Project", episodes_planned=1)
        session.add(project)
        session.commit()
        session.refresh(project)
        project_id = project.id

        storage = LocalStorageService(root=storage_root)
        artifact_service = ArtifactService(session=session, storage=storage)
        asyncio.run(
            artifact_service.save_text_artifact(
                project_id=project_id,
                template_code="episode_summary",
                content="Episode one explores the solar eclipse ritual.",
                created_by="tester",
                episode=1,
            )
        )

    app = create_application()
    with TestClient(app) as client:
        yield client, storage_root, project_id

    dependencies.reset_service_providers()
    db.reset_engine()


def test_worker_generates_keyframe(worker_setup):
    client, storage_root, project_id = worker_setup

    response = client.post(
        "/api/tasks/generate-keyframe",
        json={
            "project_id": project_id,
            "template_code": "keyframe_image",
            "instructions": "Hero stands before the eclipse.",
            "created_by": "tester",
            "episode": 1,
        },
    )

    assert response.status_code == 200
    data = response.json()
    stored = storage_root / data["storage_path"]
    assert stored.exists()
    assert stored.read_bytes().startswith(b"PLACEHOLDER_IMAGE")
