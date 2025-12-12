from typing import Any

from custom_rag.core.base_tool import BaseTool
from custom_rag.core.llm_provider import LLMProvider


class AgentExecutor:
    """Execute agentic loop where LLM decides which tools to call."""

    def __init__(
        self,
        tools: list[BaseTool],
        system_prompt: str,
        llm_provider: LLMProvider,
        max_iterations: int = 100,
    ):
        """
        Initialize agent executor.

        Args:
            tools: List of available tool instances
            system_prompt: System instructions for the LLM
            llm_provider: LLM provider instance
            max_iterations: Maximum number of iterations (default 100)
        """
        self.tools = tools
        self.system_prompt = system_prompt
        self.llm_provider = llm_provider
        self.max_iterations = max_iterations

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Run the agentic loop.

        Args:
            context: Request context

        Returns:
            Dict with output, iterations, and tools_used
        """
        user_query = context.get("prompt_objects", {}).get("query", "")

        result = self.llm_provider.execute_with_tools(
            instructions=self.system_prompt,
            user_message=user_query,
            tools=self.tools,
            max_iterations=self.max_iterations,
            context=context,
        )

        return result
