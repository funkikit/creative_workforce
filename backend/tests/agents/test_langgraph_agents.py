import pytest

from app.agents import get_agent
from app.services.image import PlaceholderImageClient
from app.services.llm import TemplateLLMClient


@pytest.mark.asyncio
async def test_text_agent_generates_markdown() -> None:
    llm = TemplateLLMClient(style="brief")
    image_client = PlaceholderImageClient()
    agent = get_agent(
        template_code="overall_spec",
        context={
            "project_name": "Stellar Saga",
            "episode": None,
            "instructions": "Highlight the mentor figure",
            "existing_summary": "",
        },
        llm=llm,
        image_client=image_client,
    )

    result = await agent.generate()

    assert "Stellar Saga" in result["content"]
    assert result["content_type"] == "text/markdown"


@pytest.mark.asyncio
async def test_image_agent_produces_placeholder_bytes() -> None:
    llm = TemplateLLMClient(style="prompt")
    image_client = PlaceholderImageClient()
    agent = get_agent(
        template_code="keyframe_image",
        context={
            "project_name": "Stellar Saga",
            "episode": 1,
            "instructions": "Hero faces the eclipse over the city skyline",
            "existing_summary": "Episode sets up the eclipse ritual.",
        },
        llm=llm,
        image_client=image_client,
    )

    result = await agent.generate()

    assert result["content"].startswith(b"PLACEHOLDER_IMAGE")
    assert result["metadata"]["prompt"].startswith("# Prompt")
