from __future__ import annotations

from typing import Any, Dict

from langgraph.graph import END, StateGraph

from app.agents.base import ArtifactAgent
from app.agents.prompts import TEXT_PROMPTS
from app.services.llm import LLMClient


class TextAgentState(Dict[str, Any]):
    content: str


class LangGraphTextAgent(ArtifactAgent):
    def __init__(
        self,
        *,
        template_code: str,
        context: Dict[str, Any],
        llm: LLMClient,
    ) -> None:
        super().__init__(context=context)
        self.template_code = template_code
        self._llm = llm
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(dict)

        async def draft(state: Dict[str, Any]) -> Dict[str, Any]:
            prompt = state["prompt"]
            content = await self._llm.generate_text(prompt=prompt)
            return {"content": content}

        graph.add_node("draft", draft)
        graph.set_entry_point("draft")
        graph.add_edge("draft", END)
        return graph.compile()

    def _render_prompt(self) -> str:
        template = TEXT_PROMPTS[self.template_code]
        return template.format(**self.context)

    async def generate(self) -> Dict[str, Any]:
        prompt = self._render_prompt()
        result = await self._graph.ainvoke({"prompt": prompt})
        return {
            "content": result["content"],
            "content_type": "text/markdown",
            "metadata": {"prompt": prompt},
        }
