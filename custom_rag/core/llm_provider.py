from abc import ABC, abstractmethod
from typing import Any, Dict, List
from custom_rag.core.base_tool import BaseTool


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model: str):
        """
        Initialize LLM provider.

        Args:
            model: Model name/ID to use
        """
        self.model = model

    @abstractmethod
    def execute_with_tools(
        self,
        instructions: str,
        user_message: str,
        tools: List[BaseTool],
        max_iterations: int,
    ) -> Dict[str, Any]:
        """
        Execute agentic loop with tools.

        Args:
            instructions: System instructions for the model
            user_message: User's input message
            tools: List of available tools
            max_iterations: Maximum number of iterations

        Returns:
            Dict with output, iterations, and tools_used
        """
        pass
