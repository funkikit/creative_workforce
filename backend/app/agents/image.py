from __future__ import annotations

from typing import Any, Dict

from langgraph.graph import END, StateGraph

from app.agents.base import ArtifactAgent
from app.agents.prompts import IMAGE_PROMPT_TEMPLATE
from app.services.image import ImageGenerationClient
from app.services.llm import LLMClient


class KeyframeImageAgent(ArtifactAgent):
    def __init__(
        self,
        *,
        context: Dict[str, Any],
        llm: LLMClient,
        image_client: ImageGenerationClient,
    ) -> None:
        super().__init__(context=context)
        self._llm = llm
        self._image_client = image_client
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(dict)

        async def draft_prompt(state: Dict[str, Any]) -> Dict[str, Any]:
            prompt_template = IMAGE_PROMPT_TEMPLATE.format(**self.context)
            prompt = await self._llm.generate_text(prompt=prompt_template, temperature=0.6)
            return {"prompt": prompt}

        async def generate_image(state: Dict[str, Any]) -> Dict[str, Any]:
            prompt = state["prompt"]
            image_bytes = await self._image_client.generate_image(prompt=prompt)
            return {"prompt": prompt, "image": image_bytes}

        graph.add_node("draft_prompt", draft_prompt)
        graph.add_node("generate_image", generate_image)
        graph.set_entry_point("draft_prompt")
        graph.add_edge("draft_prompt", "generate_image")
        graph.add_edge("generate_image", END)
        return graph.compile()

    async def generate(self) -> Dict[str, Any]:
        result = await self._graph.ainvoke({})
        return {
            "prompt": result["prompt"],
            "content": result["image"],
            "content_type": "image/png",
            "metadata": {"prompt": result["prompt"]},
        }
