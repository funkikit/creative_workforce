from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.db import get_session
from app.core.dependencies import (
    get_image_generation_client,
    get_llm_client,
    get_storage_service,
    get_task_queue_service,
)
from app.models import (
    ChatEventRead,
    ChatEventType,
    ChatMessageRead,
    ChatSessionRead,
    ChatSessionStatus,
)
from app.services.conversation import ConversationService
from app.services.image import ImageGenerationClient
from app.services.llm import LLMClient
from app.services.base import StorageService, TaskQueueService


router = APIRouter(prefix="/chat", tags=["chat"])


def _conversation_service(
    session: Session = Depends(get_session),
    llm: LLMClient = Depends(get_llm_client),
    storage: StorageService = Depends(get_storage_service),
    image_client: ImageGenerationClient = Depends(get_image_generation_client),
    task_queue: TaskQueueService = Depends(get_task_queue_service),
) -> ConversationService:
    return ConversationService(
        session=session,
        llm=llm,
        storage=storage,
        image_client=image_client,
        task_queue=task_queue,
    )


class CreateSessionRequest(BaseModel):
    project_id: Optional[int] = Field(default=None)
    title: Optional[str] = Field(default=None, max_length=200)


class ListSessionsResponse(BaseModel):
    items: list[ChatSessionRead]


class ListMessagesResponse(BaseModel):
    items: list[ChatMessageRead]


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class SendMessageResponse(BaseModel):
    user_message: ChatMessageRead
    assistant_message: ChatMessageRead
    events: list[ChatEventRead]


class ListEventsResponse(BaseModel):
    items: list[ChatEventRead]


@router.post("/sessions", response_model=ChatSessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: CreateSessionRequest,
    service: ConversationService = Depends(_conversation_service),
) -> ChatSessionRead:
    return service.create_session(project_id=payload.project_id, title=payload.title)


@router.get("/sessions", response_model=ListSessionsResponse)
def list_sessions(
    project_id: Optional[int] = Query(default=None),
    status_param: Optional[ChatSessionStatus] = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ConversationService = Depends(_conversation_service),
) -> ListSessionsResponse:
    items = service.list_sessions(project_id=project_id, status=status_param, limit=limit, offset=offset)
    return ListSessionsResponse(items=list(items))


@router.get("/sessions/{session_id}", response_model=ChatSessionRead)
def get_session(
    session_id: int,
    service: ConversationService = Depends(_conversation_service),
) -> ChatSessionRead:
    try:
        chat_session = service.get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ChatSessionRead.model_validate(chat_session)


@router.get("/sessions/{session_id}/messages", response_model=ListMessagesResponse)
def list_messages(
    session_id: int,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: ConversationService = Depends(_conversation_service),
) -> ListMessagesResponse:
    try:
        service.get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    items = service.list_messages(session_id=session_id, limit=limit, offset=offset)
    return ListMessagesResponse(items=list(items))


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    session_id: int,
    payload: SendMessageRequest,
    service: ConversationService = Depends(_conversation_service),
) -> SendMessageResponse:
    try:
        user_message, assistant_message, events = await service.process_user_message(
            session_id=session_id,
            content=payload.content,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SendMessageResponse(
        user_message=user_message,
        assistant_message=assistant_message,
        events=list(events),
    )


@router.get("/sessions/{session_id}/events", response_model=ListEventsResponse)
def list_events(
    session_id: int,
    after: Optional[int] = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    service: ConversationService = Depends(_conversation_service),
) -> ListEventsResponse:
    try:
        service.get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    items = service.list_events(session_id=session_id, after_event_id=after, limit=limit)
    return ListEventsResponse(items=list(items))
