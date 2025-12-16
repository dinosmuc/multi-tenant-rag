from abc import ABC, abstractmethod
from typing import Any

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
        tools: list[BaseTool],
        max_iterations: int,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute agentic loop with tools.

        Args:
            instructions: System instructions for the model
            user_message: User's input message
            tools: List of available tools
            max_iterations: Maximum number of iterations
            context: Request context with db, weaviate, and other resources

        Returns:
            Dict with output, iterations, and tools_used
        """
        pass

    @abstractmethod
    def create_plan(self, user_query: str, system_prompt: str) -> str:
        """
        Create a strategic plan using the LLM.

        Args:
            user_query: The user's original query
            system_prompt: The system prompt for context

        Returns:
            A strategic plan as a string
        """
        pass
