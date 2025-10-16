from sqlmodel import select

from app.core import db
from app.models.artifacts import Artifact
from app.models.projects import Project


def test_init_db_creates_tables(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'app.db'}")
    db.reset_engine()
    db.init_db()

    with db.session() as session:
        project = Project(name="Test Project")
        session.add(project)
        session.commit()
        session.refresh(project)

        artifact = Artifact(
            project_id=project.id,
            template_code="overall_spec",
            storage_path="projects/test/path.md",
            created_by="tester",
        )
        session.add(artifact)
        session.commit()

        artifacts = session.exec(select(Artifact).where(Artifact.project_id == project.id)).all()

    assert len(artifacts) == 1
    assert artifacts[0].template_code == "overall_spec"
