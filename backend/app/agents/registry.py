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
    enriched.setdefault("project_name", "Untitled Project")
    enriched.setdefault("instructions", "")
    enriched.setdefault("existing_summary", enriched.get("previous_artifact", ""))
    if episode:
        enriched.setdefault("episode_number", episode)
        enriched.setdefault("episode_label", f"Episode {episode}")
    else:
        enriched.setdefault("episode_number", 1)
        enriched.setdefault("episode_label", "Main")
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
            raise ValueError("Image generation client is required for keyframe image agent")
        return KeyframeImageAgent(context=extended_context, llm=llm, image_client=image_client)

    raise ValueError(f"Unsupported template code for agent: {template_code}")
