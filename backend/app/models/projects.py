from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ProjectBase(SQLModel):
    name: str = Field(index=True)
    description: Optional[str] = None
    episodes_planned: int = Field(default=1, ge=1)


class Project(ProjectBase, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
