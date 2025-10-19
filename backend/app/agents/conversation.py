from __future__ import annotations

from __future__ import annotations

import re
from textwrap import dedent
from typing import Sequence

from app.core.templates import EPISODE_TEMPLATES
from app.models import ChatEventType, ChatMessage, ChatSession
from app.services.llm import LLMClient


TEMPLATE_LABELS = {
    "overall_spec": "作品全体仕様書",
    "character_design": "キャラクター設定",
    "background_sample": "背景サンプル",
    "episode_summary": "エピソード概要",
    "episode_script": "エピソード脚本",
    "storyboard_table": "絵コンテ表",
    "keyframe_image": "キーフレーム画像",
}

TEMPLATE_KEYWORDS = {
    "episode_summary": ["エピソード概要", "エピソードサマリー", "あらすじ", "ストーリー概要"],
    "episode_script": ["脚本", "台本", "シナリオ"],
    "storyboard_table": ["絵コンテ", "ストーリーボード"],
    "character_design": ["キャラ", "キャラクター", "人物設定", "デザイン"],
    "background_sample": ["背景", "美術設定", "ロケーション"],
    "keyframe_image": ["キーフレーム", "ビジュアル", "イメージボード", "画像"],
    "overall_spec": ["全体仕様", "世界観", "コンセプト", "概要"],
}

TEMPLATE_PRIORITY = list(TEMPLATE_KEYWORDS.keys())

ACTION_KEYWORDS = ["生成", "作成", "作って", "出力", "描いて", "用意", "ください", "お願いします"]
SUMMARY_KEYWORDS = ["進捗", "状況", "まとめ", "足りない", "未完了", "完了した", "残り"]


class ConversationAgent:
    """LangGraph ではなく最小限の LLM 呼び出しで会話を進行する PoC エージェント."""

    def __init__(
        self,
        *,
        llm: LLMClient,
        session: ChatSession,
        history: Sequence[ChatMessage],
        project: dict | None,
    ) -> None:
        self._llm = llm
        self._session = session
        self._history = history
        self._project = project

    async def generate_reply(
        self,
        user_message: str,
    ) -> tuple[str, dict, list[dict]]:
        intent = self._detect_intent(user_message)

        if intent["intent"] == "artifact.generate":
            template_label = TEMPLATE_LABELS[intent["template_code"]]
            reply = f"{template_label}の生成を開始します。準備ができ次第、お知らせします。"
            extra = intent
            events = [
                {
                    "type": ChatEventType.STATUS.value,
                    "payload": {
                        "phase": "queued",
                        "intent": intent["intent"],
                        "template_code": intent["template_code"],
                        "template_label": template_label,
                    },
                }
            ]
            return reply, extra, events

        if intent["intent"] == "project.summary":
            reply = "進捗状況を整理して共有します。"
            extra = intent
            events = [
                {
                    "type": ChatEventType.STATUS.value,
                    "payload": {
                        "phase": "requested",
                        "intent": intent["intent"],
                    },
                }
            ]
            return reply, extra, events

        if intent["intent"] == "chat.awaiting_episode":
            template_label = TEMPLATE_LABELS[intent["template_code"]]
            reply = f"{template_label}を生成するには対象エピソード番号を教えてください。"
            extra = intent
            return reply, extra, []

        prompt = self._render_smalltalk_prompt(user_message=user_message)
        reply = await self._llm.generate_text(prompt=prompt, temperature=0.5)
        extra = {"intent": "chat.smalltalk"}
        events: list[dict] = []
        return reply, extra, events

    def _render_smalltalk_prompt(self, *, user_message: str) -> str:
        project_context = ""
        if self._project:
            project_context = dedent(
                f"""
                - プロジェクト名: {self._project.get("name") or "未設定"}
                - 概要: {self._project.get("description") or "説明なし"}
                - 予定話数: {self._project.get("episodes_planned")}
                """
            ).strip()

        history_lines = "\n".join(
            f"{message.role.value.upper()}: {message.content}"
            for message in self._history
        )

        prompt = dedent(
            f"""
            あなたはクリエイティブチームを支援するアシスタントです。
            以下の会話履歴と最新メッセージを踏まえて、丁寧な日本語で回答してください。
            必要に応じて次の行動を提案し、生成済みの成果物があれば参照を促してください。

            ## プロジェクト情報
            {project_context or "（未設定）"}

            ## これまでの会話
            {history_lines or "まだ会話履歴はありません。"}

            ## ユーザーからの最新メッセージ
            USER: {user_message}
            """
        ).strip()
        return prompt

    def _detect_intent(self, user_message: str) -> dict:
        normalized = user_message.strip()
        lowered = normalized.lower()

        if any(keyword in normalized for keyword in SUMMARY_KEYWORDS):
            return {"intent": "project.summary"}

        for template_code in TEMPLATE_PRIORITY:
            keywords = TEMPLATE_KEYWORDS[template_code]
            if any(keyword in normalized for keyword in keywords) and any(
                action in normalized for action in ACTION_KEYWORDS
            ):
                episode = self._extract_episode(lowered)
                if template_code in EPISODE_TEMPLATES and episode is None:
                    return {"intent": "chat.awaiting_episode", "template_code": template_code}
                return {
                    "intent": "artifact.generate",
                    "template_code": template_code,
                    "template_label": TEMPLATE_LABELS[template_code],
                    "episode": episode,
                    "instructions": normalized,
                }

        return {"intent": "chat.smalltalk"}

    @staticmethod
    def _extract_episode(message: str) -> int | None:
        episode_match = re.search(r"(?:第|episode[\s_]*)(\d+)(?:話|話目|章|episode|エピソード)?", message, re.IGNORECASE)
        if episode_match:
            try:
                return int(episode_match.group(1))
            except ValueError:
                return None
        simple_match = re.search(r"(\d+)\s*(?:話|episode|ep)", message, re.IGNORECASE)
        if simple_match:
            try:
                return int(simple_match.group(1))
            except ValueError:
                return None
        return None
