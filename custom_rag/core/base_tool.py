from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Tool identifier.

        Returns:
            Tool name used for identification
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Tool description shown to the LLM.

        Returns:
            Description of what the tool does
        """
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """
        JSON schema of expected arguments.

        Returns:
            JSON schema dict defining tool parameters
        """
        pass

    @abstractmethod
    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Execute the tool with given arguments and context.

        Args:
            args: Tool arguments matching the parameters schema
            context: Request context containing user data and connections

        Returns:
            Tool execution result
        """
        pass
