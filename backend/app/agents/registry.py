from __future__ import annotations

from typing import Any, Dict

from app.agents.base import ArtifactAgent
from app.agents.image import KeyframeImageAgent
from app.agents.text import LangGraphTextAgent
from app.services.image import ImageGenerationClient
from app.services.llm import LLMClient

TEXT_TEMPLATES = {
    "overall_spec",
    "character_design",
    "background_sample",
    "episode_summary",
    "episode_script",
    "storyboard_table",
}


def enrich_context(template_code: str, context: Dict[str, Any]) -> Dict[str, Any]:
    enriched = context.copy()
    episode = enriched.get("episode")
    enriched.setdefault("project_name", "無題のプロジェクト")
    enriched.setdefault("instructions", "")
    enriched.setdefault("existing_summary", enriched.get("previous_artifact", ""))
    if episode:
        enriched.setdefault("episode_number", episode)
        enriched.setdefault("episode_label", f"第{episode}話")
    else:
        enriched.setdefault("episode_number", 1)
        enriched.setdefault("episode_label", "メイン")
    return enriched


def get_agent(
    *,
    template_code: str,
    context: Dict[str, Any],
    llm: LLMClient,
    image_client: ImageGenerationClient | None = None,
) -> ArtifactAgent:
    extended_context = enrich_context(template_code, context)

    if template_code in TEXT_TEMPLATES:
        return LangGraphTextAgent(template_code=template_code, context=extended_context, llm=llm)

    if template_code == "keyframe_image":
        if image_client is None:
            raise ValueError("キーフレーム画像エージェントには画像生成クライアントが必要です")
        return KeyframeImageAgent(context=extended_context, llm=llm, image_client=image_client)

    raise ValueError(f"このテンプレートコードに対応するエージェントは存在しません: {template_code}")
