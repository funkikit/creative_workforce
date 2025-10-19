from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core import db, dependencies
from app.main import create_application


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'chat.db'}")
    monkeypatch.setenv("LOCAL_STORAGE_ROOT", str(tmp_path / "storage"))
    db.reset_engine()
    dependencies.reset_service_providers()

    app = create_application()
    with TestClient(app) as test_client:
        yield test_client

    dependencies.reset_service_providers()
    db.reset_engine()


def test_chat_workflow(client: TestClient):
    # セッション作成
    create_resp = client.post("/api/chat/sessions", json={"title": "初回相談"})
    assert create_resp.status_code == 201
    session = create_resp.json()

    # メッセージ送信
    send_resp = client.post(
        f"/api/chat/sessions/{session['id']}/messages",
        json={"content": "世界観の方向性を教えてください。"},
    )
    assert send_resp.status_code == 201
    payload = send_resp.json()
    assert payload["user_message"]["role"] == "user"
    assert payload["assistant_message"]["role"] == "assistant"
    assert payload["assistant_message"]["content"]

    # メッセージ一覧
    list_resp = client.get(f"/api/chat/sessions/{session['id']}/messages")
    assert list_resp.status_code == 200
    messages = list_resp.json()["items"]
    assert len(messages) == 2

    # イベント一覧
    events_resp = client.get(f"/api/chat/sessions/{session['id']}/events")
    assert events_resp.status_code == 200
    events = events_resp.json()["items"]
    assert any(event["type"] == "message" for event in events)


def test_chat_can_trigger_artifact_generation(client: TestClient):
    project_resp = client.post(
        "/api/projects",
        json={"name": "Chat Driven", "episodes_planned": 1},
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    session_resp = client.post(
        "/api/chat/sessions",
        json={"project_id": project_id, "title": "制作相談"},
    )
    assert session_resp.status_code == 201
    session_id = session_resp.json()["id"]

    send_resp = client.post(
        f"/api/chat/sessions/{session_id}/messages",
        json={"content": "第1話のエピソード概要を生成してください"},
    )
    assert send_resp.status_code == 201
    payload = send_resp.json()
    assert "✅" in payload["assistant_message"]["content"]

    events = payload["events"]
    assert any(event["type"] == "artifact_update" for event in events)

    # 成果物が保存されていることを確認
    artifacts_resp = client.get(f"/api/projects/{project_id}/artifacts")
    assert artifacts_resp.status_code == 200
    artifacts = artifacts_resp.json()
    assert artifacts
    assert artifacts[0]["template_code"] == "episode_summary"
