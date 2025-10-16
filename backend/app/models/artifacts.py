from datetime import datetime
from typing import Literal, Optional

from sqlmodel import Field, SQLModel


class Artifact(SQLModel, table=True):
    __tablename__ = "artifacts"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    template_code: str = Field(index=True)
    version: int = Field(default=1)
    status: Literal["draft", "final"] = Field(default="draft")
    storage_path: str
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
