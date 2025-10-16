import asyncio
from pathlib import Path

import pytest
from sqlmodel import select

from app.core import db
from app.models import Artifact, Project
from app.services.artifacts import ArtifactService
from app.services.local import LocalStorageService


@pytest.fixture
def sqlite_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'app.db'}")
    db.reset_engine()
    db.init_db()
    yield tmp_path
    db.reset_engine()


@pytest.mark.asyncio
async def test_save_text_artifact_persists_file(sqlite_env: Path) -> None:
    storage_root = sqlite_env / "storage"
    storage = LocalStorageService(root=storage_root)
    with db.session() as session:
        project = Project(name="Test Project")
        session.add(project)
        session.commit()
        session.refresh(project)

        service = ArtifactService(session=session, storage=storage)
        artifact = await service.save_text_artifact(
            project_id=project.id,
            template_code="overall_spec",
            content="Hello World",
            created_by="tester",
        )

        stored = storage.root / artifact.storage_path
        data = await storage.load_bytes(artifact.storage_path)

    assert artifact.version == 1
    assert stored.exists()
    assert data.decode("utf-8") == "Hello World"


@pytest.mark.asyncio
async def test_save_text_artifact_increments_version(sqlite_env: Path) -> None:
    storage_root = sqlite_env / "storage_versions"
    storage = LocalStorageService(root=storage_root)
    with db.session() as session:
        project = Project(name="Versioned Project")
        session.add(project)
        session.commit()
        session.refresh(project)

        service = ArtifactService(session=session, storage=storage)
        await service.save_text_artifact(
            project_id=project.id,
            template_code="overall_spec",
            content="v1",
            created_by="tester",
        )
        artifact_v2 = await service.save_text_artifact(
            project_id=project.id,
            template_code="overall_spec",
            content="v2",
            created_by="tester",
        )

        stored_files = list((storage_root / f"projects/{project.id}/overall_spec").rglob("*.md"))
        versions = session.exec(
            select(Artifact.version).where(
                Artifact.project_id == project.id, Artifact.template_code == "overall_spec"
            )
        ).all()

    assert artifact_v2.version == 2
    assert len(stored_files) == 2
    assert sorted(versions) == [1, 2]


@pytest.mark.asyncio
async def test_save_binary_artifact_persists_bytes(sqlite_env: Path) -> None:
    storage_root = sqlite_env / "binary_storage"
    storage = LocalStorageService(root=storage_root)
    with db.session() as session:
        project = Project(name="Binary Project")
        session.add(project)
        session.commit()
        session.refresh(project)

        service = ArtifactService(session=session, storage=storage)
        artifact = await service.save_binary_artifact(
            project_id=project.id,
            template_code="keyframe_image",
            data=b"\x89PNGstub",
            created_by="tester",
            content_type="image/png",
        )

        stored = storage.root / artifact.storage_path
        payload = await storage.load_bytes(artifact.storage_path)

    assert stored.exists()
    assert payload == b"\x89PNGstub"
