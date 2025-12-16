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

        # OPENAI api call to make a plan given the current system prompt and user query
        plan = self._create_plan(user_query)

        # Append the plan to the system prompt
        enhanced_instructions = f"{self.system_prompt}\n\nPLAN TO FOLLOW:\n{plan}"

        # Execute with the enhanced instructions
        result = self.llm_provider.execute_with_tools(
            instructions=enhanced_instructions,
            user_message=user_query,
            tools=self.tools,
            max_iterations=self.max_iterations,
            context=context,
        )

        return result

    def _create_plan(self, user_query: str) -> str:
        """
        Create a strategic plan using the LLM provider.

        Args:
            user_query: The user's query

        Returns:
            A strategic plan as a string
        """
        return self.llm_provider.create_plan(user_query, self.system_prompt)
