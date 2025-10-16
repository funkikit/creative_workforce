from abc import ABC, abstractmethod
from typing import Any, Dict


class ArtifactAgent(ABC):
    """Base class for artifact-specific agents."""

    name: str

    def __init__(self, *, context: Dict[str, Any]):
        self.context = context

    @abstractmethod
    async def generate(self) -> Dict[str, Any]:
        """Produce or refine an artifact payload."""
        raise NotImplementedError
