from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core import db, dependencies
from app.main import create_application


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    storage_root = tmp_path / "storage"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'api.db'}")
    monkeypatch.setenv("LOCAL_STORAGE_ROOT", str(storage_root))
    db.reset_engine()
    dependencies.reset_service_providers()

    app = create_application()
    with TestClient(app) as test_client:
        yield test_client, storage_root

    dependencies.reset_service_providers()
    db.reset_engine()


def test_project_workflow(client):
    http_client, storage_root = client

    create_resp = http_client.post(
        "/api/projects",
        json={"name": "Pilot", "description": "Test", "episodes_planned": 2},
    )
    assert create_resp.status_code == 201
    project = create_resp.json()

    artifact_payload = {
        "template_code": "overall_spec",
        "content": "# Overview",
        "created_by": "tester",
        "status": "draft",
        "content_type": "text/markdown",
    }
    artifact_resp = http_client.post(
        f"/api/projects/{project['id']}/artifacts",
        json=artifact_payload,
    )
    assert artifact_resp.status_code == 201
    artifact = artifact_resp.json()

    stored_file = storage_root / artifact["storage_path"]
    assert stored_file.exists()

    list_resp = http_client.get(f"/api/projects/{project['id']}/artifacts")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    progress_resp = http_client.get(f"/api/projects/{project['id']}/progress")
    assert progress_resp.status_code == 200
    progress = progress_resp.json()
    assert progress["global"]["completed"] == ["overall_spec"]
    assert "character_design" in progress["global"]["pending"]


def test_episode_artifact_requires_episode(client):
    http_client, _ = client
    project_resp = http_client.post("/api/projects", json={"name": "Show"})
    project_id = project_resp.json()["id"]

    bad_resp = http_client.post(
        f"/api/projects/{project_id}/artifacts",
        json={
            "template_code": "episode_summary",
            "content": "Episode Outline",
            "created_by": "tester",
        },
    )
    assert bad_resp.status_code == 400
