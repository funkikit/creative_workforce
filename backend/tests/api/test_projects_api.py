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

    artifact_id = artifact["id"]
    content_resp = http_client.get(
        f"/api/projects/{project['id']}/artifacts/{artifact_id}"
    )
    assert content_resp.status_code == 200
    assert "Overview" in content_resp.json()["content"]

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


def test_generate_overall_spec_agent_creates_artifact(client):
    http_client, storage_root = client
    project_resp = http_client.post(
        "/api/projects",
        json={"name": "Agent Project", "description": "", "episodes_planned": 1},
    )
    project_id = project_resp.json()["id"]

    generation_resp = http_client.post(
        f"/api/projects/{project_id}/artifacts/overall_spec/generate",
        json={"created_by": "tester", "instructions": "Focus on rival"},
    )
    assert generation_resp.status_code == 200
    payload = generation_resp.json()
    artifact_path = payload["artifact"]["storage_path"]
    artifact_id = payload["artifact"]["id"]

    stored_file = storage_root / artifact_path
    assert stored_file.exists()
    assert "Agent Project" in stored_file.read_text()

    content_resp = http_client.get(
        f"/api/projects/{project_id}/artifacts/{artifact_id}"
    )
    assert content_resp.status_code == 200
    assert "Agent Project" in content_resp.json()["content"]


def test_generate_keyframe_enqueues_task(client):
    http_client, _ = client
    project_resp = http_client.post(
        "/api/projects",
        json={"name": "Keyframe Project", "episodes_planned": 2},
    )
    project_id = project_resp.json()["id"]

    queue_resp = http_client.post(
        f"/api/projects/{project_id}/artifacts/keyframe_image/generate",
        json={
            "created_by": "tester",
            "instructions": "Show the hero awaiting the eclipse",
            "episode": 1,
        },
    )
    assert queue_resp.status_code == 202

    task_queue = dependencies.get_task_queue_service()
    assert len(task_queue.pending()) == 1
    job = task_queue.pending()[0]
    assert job.payload["task_type"] == "generate_keyframe"
