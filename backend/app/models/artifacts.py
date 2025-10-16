from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ArtifactBase(SQLModel):
    project_id: int = Field(index=True)
    template_code: str = Field(index=True)
    episode: Optional[int] = Field(default=None, index=True)
    version: int = Field(default=1)
    status: str = Field(default="draft")
    storage_path: str
    created_by: str


class Artifact(ArtifactBase, table=True):
    __tablename__ = "artifacts"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ArtifactRead(ArtifactBase):
    id: int
    created_at: datetime
    updated_at: datetime
