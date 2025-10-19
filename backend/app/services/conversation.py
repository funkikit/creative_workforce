from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sqlmodel import Session, select

from app.core.templates import validate_template_code
from app.models import (
    Artifact,
    ChatEvent,
    ChatEventRead,
    ChatEventType,
    ChatMessage,
    ChatMessageRead,
    ChatMessageRole,
    ChatSession,
    ChatSessionRead,
    ChatSessionStatus,
)
from app.services.artifacts import ArtifactService
from app.services.base import StorageService, TaskQueueService
from app.services.image import ImageGenerationClient
from app.services.llm import LLMClient
from app.services.progress import ProjectProgressService
from app.services.projects import ProjectService

TEMPLATE_LABELS = {
    "overall_spec": "作品全体仕様書",
    "character_design": "キャラクター設定",
    "background_sample": "背景サンプル",
    "episode_summary": "エピソード概要",
    "episode_script": "エピソード脚本",
    "storyboard_table": "絵コンテ表",
    "keyframe_image": "キーフレーム画像",
}


def _to_session_read(instance: ChatSession) -> ChatSessionRead:
    return ChatSessionRead.model_validate(instance)


def _to_message_read(instance: ChatMessage) -> ChatMessageRead:
    return ChatMessageRead.model_validate(instance)


def _to_event_read(instance: ChatEvent) -> ChatEventRead:
    return ChatEventRead.model_validate(instance)


@dataclass
class ConversationService:
    session: Session
    llm: LLMClient
    storage: StorageService
    image_client: ImageGenerationClient
    task_queue: TaskQueueService

    # Session management -----------------------------------------------------------------
    def create_session(
        self,
        *,
        project_id: int | None,
        title: str | None = None,
    ) -> ChatSessionRead:
        chat_session = ChatSession(project_id=project_id, title=title)
        self.session.add(chat_session)
        self.session.commit()
        self.session.refresh(chat_session)
        return _to_session_read(chat_session)

    def list_sessions(
        self,
        *,
        project_id: int | None = None,
        status: ChatSessionStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[ChatSessionRead]:
        query = select(ChatSession).order_by(ChatSession.updated_at.desc())
        if project_id is not None:
            query = query.where(ChatSession.project_id == project_id)
        if status is not None:
            query = query.where(ChatSession.status == status)
        query = query.offset(offset).limit(limit)
        sessions = self.session.exec(query).all()
        return [_to_session_read(item) for item in sessions]

    def get_session(self, session_id: int) -> ChatSession:
        chat_session = self.session.get(ChatSession, session_id)
        if chat_session is None:
            raise ValueError(f"会話セッション {session_id} が見つかりません")
        return chat_session

    # Messages ---------------------------------------------------------------------------
    def list_messages(
        self,
        *,
        session_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[ChatMessageRead]:
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        messages = self.session.exec(query).all()
        return [_to_message_read(message) for message in messages]

    def _persist_message(
        self,
        *,
        session_id: int,
        role: ChatMessageRole,
        content: str,
        extra: dict | None = None,
    ) -> ChatMessage:
        record = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            extra=extra,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        # セッション更新日時を更新
        chat_session = self.get_session(session_id)
        chat_session.updated_at = record.created_at
        self.session.add(chat_session)
        self.session.commit()
        return record

    # Events -----------------------------------------------------------------------------
    def _create_event(
        self,
        *,
        session_id: int,
        event_type: ChatEventType,
        payload: dict,
    ) -> ChatEvent:
        event = ChatEvent(session_id=session_id, type=event_type, payload=payload)
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def list_events(
        self,
        *,
        session_id: int,
        after_event_id: int | None = None,
        limit: int = 100,
    ) -> Sequence[ChatEventRead]:
        query = select(ChatEvent).where(ChatEvent.session_id == session_id).order_by(ChatEvent.id.asc())
        if after_event_id is not None:
            query = query.where(ChatEvent.id > after_event_id)
        query = query.limit(limit)
        events = self.session.exec(query).all()
        return [_to_event_read(event) for event in events]

    # Conversation -----------------------------------------------------------------------
    async def process_user_message(
        self,
        *,
        session_id: int,
        content: str,
    ) -> tuple[ChatMessageRead, ChatMessageRead, list[ChatEventRead]]:
        chat_session = self.get_session(session_id)
        user_message = self._persist_message(
            session_id=session_id,
            role=ChatMessageRole.USER,
            content=content,
        )

        history = self._recent_messages(session_id=session_id, limit=8)
        project_details = self._project_context(project_id=chat_session.project_id)

        from app.agents.conversation import ConversationAgent

        agent = ConversationAgent(
            llm=self.llm,
            session=chat_session,
            history=history,
            project=project_details,
        )
        reply, extra, events = await agent.generate_reply(content)

        assistant_message = self._persist_message(
            session_id=session_id,
            role=ChatMessageRole.ASSISTANT,
            content=reply,
            extra=extra,
        )

        persisted_events = []
        for event in events:
            persisted = self._create_event(
                session_id=session_id,
                event_type=event["type"],
                payload=event["payload"],
            )
            persisted_events.append(persisted)

        assistant_message, action_events = await self._execute_intent(
            chat_session=chat_session,
            assistant_message=assistant_message,
            metadata=extra or {},
            user_message=content,
        )
        persisted_events.extend(action_events)

        message_event = self._create_event(
            session_id=session_id,
            event_type=ChatEventType.MESSAGE,
            payload={"message_id": assistant_message.id, "role": ChatMessageRole.ASSISTANT.value},
        )
        persisted_events.append(message_event)

        assistant_message_refreshed = self.session.get(ChatMessage, assistant_message.id)

        return (
            _to_message_read(user_message),
            _to_message_read(assistant_message_refreshed or assistant_message),
            [_to_event_read(event) for event in persisted_events],
        )

    def _recent_messages(self, *, session_id: int, limit: int) -> Sequence[ChatMessage]:
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = self.session.exec(query).all()
        return list(reversed(messages))

    def _project_context(self, *, project_id: int | None) -> dict | None:
        if project_id is None:
            return None
        project_service = ProjectService(session=self.session)
        project = project_service.get_project(project_id)
        if project is None:
            return None
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "episodes_planned": project.episodes_planned,
        }

    async def _execute_intent(
        self,
        *,
        chat_session: ChatSession,
        assistant_message: ChatMessage,
        metadata: dict,
        user_message: str,
    ) -> tuple[ChatMessage, list[ChatEvent]]:
        intent = metadata.get("intent")
        events: list[ChatEvent] = []

        if intent == "artifact.generate":
            artifact_events = await self._handle_artifact_generation(
                chat_session=chat_session,
                assistant_message=assistant_message,
                metadata=metadata,
                user_message=user_message,
            )
            events.extend(artifact_events)

        if intent == "project.summary":
            summary_events = self._handle_progress_summary(
                chat_session=chat_session,
                assistant_message=assistant_message,
            )
            events.extend(summary_events)

        return assistant_message, events

    async def _handle_artifact_generation(
        self,
        *,
        chat_session: ChatSession,
        assistant_message: ChatMessage,
        metadata: dict,
        user_message: str,
    ) -> list[ChatEvent]:
        template_code = metadata.get("template_code")
        if template_code is None:
            return []

        try:
            validate_template_code(template_code)
        except ValueError as exc:
            assistant_message.content += f"\n\n⚠️ テンプレートが判別できませんでした: {exc}"
            self.session.add(assistant_message)
            self.session.commit()
            return [
                self._create_event(
                    session_id=assistant_message.session_id,
                    event_type=ChatEventType.STATUS,
                    payload={
                        "phase": "failed",
                        "reason": str(exc),
                        "intent": "artifact.generate",
                    },
                )
            ]

        if chat_session.project_id is None:
            assistant_message.content += "\n\n⚠️ プロジェクトが紐づいていないため、成果物を生成できません。"
            self.session.add(assistant_message)
            self.session.commit()
            return [
                self._create_event(
                    session_id=assistant_message.session_id,
                    event_type=ChatEventType.STATUS,
                    payload={
                        "phase": "failed",
                        "reason": "project_missing",
                        "intent": "artifact.generate",
                    },
                )
            ]

        project_service = ProjectService(session=self.session)
        project = project_service.get_project(chat_session.project_id)
        if project is None:
            assistant_message.content += "\n\n⚠️ プロジェクト情報を取得できず、生成を中断しました。"
            self.session.add(assistant_message)
            self.session.commit()
            return [
                self._create_event(
                    session_id=assistant_message.session_id,
                    event_type=ChatEventType.STATUS,
                    payload={
                        "phase": "failed",
                        "reason": "project_not_found",
                        "intent": "artifact.generate",
                    },
                )
            ]

        instructions = metadata.get("instructions") or user_message
        episode = metadata.get("episode")

        existing_summary = await self._load_previous_artifact_summary(
            project_id=project.id,
            template_code=template_code,
            episode=episode,
        )

        context = {
            "project_name": project.name,
            "project_description": project.description or "",
            "episode": episode,
            "instructions": instructions,
            "existing_summary": existing_summary,
        }

        from app.agents import get_agent

        agent = get_agent(
            template_code=template_code,
            context=context,
            llm=self.llm,
            image_client=self.image_client,
        )
        result = await agent.generate()

        artifact_service = ArtifactService(session=self.session, storage=self.storage)
        created_by = metadata.get("created_by", "conversation-agent")

        if str(result.get("content_type", "")).startswith("image"):
            artifact = await artifact_service.save_binary_artifact(
                project_id=project.id,
                template_code=template_code,
                data=result["content"],
                created_by=created_by,
                episode=episode,
                status="final",
                content_type=result.get("content_type", "image/png"),
            )
        else:
            artifact = await artifact_service.save_text_artifact(
                project_id=project.id,
                template_code=template_code,
                content=result["content"],
                created_by=created_by,
                episode=episode,
                status="generated",
                content_type=result.get("content_type", "text/markdown"),
            )

        template_label = metadata.get("template_label") or template_code
        assistant_message.content += f"\n\n✅ {template_label}を生成しました（ID: {artifact.id}）。"
        extra_data = assistant_message.extra or {}
        extra_data.update(
            {
                "artifact_id": artifact.id,
                "artifact_template": template_code,
            }
        )
        assistant_message.extra = extra_data
        self.session.add(assistant_message)
        self.session.commit()
        self.session.refresh(assistant_message)

        status_event = self._create_event(
            session_id=assistant_message.session_id,
            event_type=ChatEventType.STATUS,
            payload={
                "phase": "completed",
                "intent": "artifact.generate",
                "template_code": template_code,
                "artifact_id": artifact.id,
            },
        )
        artifact_event = self._create_event(
            session_id=assistant_message.session_id,
            event_type=ChatEventType.ARTIFACT_UPDATE,
            payload={
                "artifact_id": artifact.id,
                "project_id": artifact.project_id,
                "template_code": artifact.template_code,
                "episode": artifact.episode,
                "storage_path": artifact.storage_path,
            },
        )
        return [status_event, artifact_event]

    def _handle_progress_summary(
        self,
        *,
        chat_session: ChatSession,
        assistant_message: ChatMessage,
    ) -> list[ChatEvent]:
        if chat_session.project_id is None:
            assistant_message.content += "\n\n⚠️ プロジェクトが紐づいていないため、進捗を取得できません。"
            self.session.add(assistant_message)
            self.session.commit()
            return [
                self._create_event(
                    session_id=assistant_message.session_id,
                    event_type=ChatEventType.STATUS,
                    payload={
                        "phase": "failed",
                        "reason": "project_missing",
                        "intent": "project.summary",
                    },
                )
            ]

        progress_service = ProjectProgressService(session=self.session)
        summary = progress_service.summarize(chat_session.project_id)
        summary_text = self._format_progress_summary(summary)
        assistant_message.content += f"\n\n{summary_text}"
        extra_data = assistant_message.extra or {}
        extra_data.update({"summary": summary})
        assistant_message.extra = extra_data
        self.session.add(assistant_message)
        self.session.commit()
        self.session.refresh(assistant_message)

        status_event = self._create_event(
            session_id=assistant_message.session_id,
            event_type=ChatEventType.STATUS,
            payload={
                "phase": "completed",
                "intent": "project.summary",
                "summary": summary,
            },
        )
        return [status_event]

    def _format_progress_summary(self, summary: dict) -> str:
        global_completed = summary.get("global", {}).get("completed", [])
        global_pending = summary.get("global", {}).get("pending", [])
        lines = ["進捗サマリー:"]
        completed_text = ", ".join(TEMPLATE_LABELS.get(code, code) for code in global_completed) if global_completed else "なし"
        pending_text = ", ".join(TEMPLATE_LABELS.get(code, code) for code in global_pending) if global_pending else "なし"
        lines.append(f"- グローバル完了: {completed_text}")
        lines.append(f"- グローバル未完了: {pending_text}")

        episodes = summary.get("episodes", [])
        for episode in episodes:
            completed_items = episode.get("completed", [])
            pending_items = episode.get("pending", [])
            completed = ", ".join(TEMPLATE_LABELS.get(code, code) for code in completed_items) or "なし"
            pending = ", ".join(TEMPLATE_LABELS.get(code, code) for code in pending_items) or "なし"
            lines.append(
                f"- エピソード{episode.get('episode')}: 完了 {completed} / 未完了 {pending}"
            )
        return "\n".join(lines)

    async def _load_previous_artifact_summary(
        self,
        *,
        project_id: int,
        template_code: str,
        episode: int | None,
    ) -> str:
        query = (
            select(Artifact)
            .where(Artifact.project_id == project_id, Artifact.template_code == template_code)
            .order_by(Artifact.version.desc())
        )
        if episode is None:
            query = query.where(Artifact.episode.is_(None))
        else:
            query = query.where(Artifact.episode == episode)

        previous = self.session.exec(query).first()
        if previous is None:
            return ""
        try:
            data = await self.storage.load_bytes(previous.storage_path)
            return data.decode("utf-8", errors="ignore")[:1200]
        except FileNotFoundError:
            return ""
