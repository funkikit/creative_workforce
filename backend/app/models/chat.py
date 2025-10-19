from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class ChatSessionStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class ChatSessionBase(SQLModel):
    project_id: Optional[int] = Field(default=None, index=True)
    title: Optional[str] = Field(default=None, max_length=200)
    status: ChatSessionStatus = Field(default=ChatSessionStatus.ACTIVE)


class ChatSession(ChatSessionBase, table=True):
    __tablename__ = "chat_sessions"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )


class ChatSessionRead(ChatSessionBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ChatMessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessageBase(SQLModel):
    session_id: int = Field(index=True, foreign_key="chat_sessions.id")
    role: ChatMessageRole
    content: str
    extra: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))


class ChatMessage(ChatMessageBase, table=True):
    __tablename__ = "chat_messages"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatMessageRead(ChatMessageBase):
    id: int
    created_at: datetime


class ChatEventType(StrEnum):
    MESSAGE = "message"
    STATUS = "status"
    ARTIFACT_UPDATE = "artifact_update"
    TASK_PROGRESS = "task_progress"


class ChatEventBase(SQLModel):
    session_id: int = Field(index=True, foreign_key="chat_sessions.id")
    type: ChatEventType
    payload: dict = Field(sa_column=Column(JSON))


class ChatEvent(ChatEventBase, table=True):
    __tablename__ = "chat_events"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatEventRead(ChatEventBase):
    id: int
    created_at: datetime
