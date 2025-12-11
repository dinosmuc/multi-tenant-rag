import json
import os
from typing import Any

from openai import OpenAI

from custom_rag.core.base_tool import BaseTool
from custom_rag.core.llm_provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI implementation using Responses API."""

    def __init__(self, model: str, reasoning_effort: str | None = None):
        """
        Initialize OpenAI provider.

        Args:
            model: Model name (e.g., 'gpt-4o', 'gpt-4', 'o1', 'o3')
            reasoning_effort: Reasoning effort level for reasoning models
                             ('low', 'medium', 'high')
        """
        super().__init__(model)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.reasoning_effort = reasoning_effort
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def execute_with_tools(
        self,
        instructions: str,
        user_message: str,
        tools: list[BaseTool],
        max_iterations: int,
    ) -> dict[str, Any]:
        """
        Execute agentic loop using OpenAI Responses API.

        Args:
            instructions: System instructions
            user_message: User's message
            tools: Available tools
            max_iterations: Maximum iterations

        Returns:
            Dict with output, iterations, and tools_used
        """
        tool_map = {tool.name: tool for tool in tools}
        tools_used = []
        iteration = 0
        previous_response_id = None

        openai_tools = self._convert_tools_to_openai_format(tools)

        while iteration < max_iterations:
            iteration += 1

            input_data = user_message if iteration == 1 else None

            request_params = {
                "model": self.model,
                "instructions": instructions,
                "input": input_data,
                "tools": openai_tools if openai_tools else None,
                "previous_response_id": previous_response_id,
            }

            if self.reasoning_effort:
                request_params["reasoning"] = {"effort": self.reasoning_effort}

            response = self.client.responses.create(**request_params)

            previous_response_id = response.id

            if hasattr(response, "usage") and response.usage:
                self.total_input_tokens += getattr(response.usage, "input_tokens", 0)
                self.total_output_tokens += getattr(response.usage, "output_tokens", 0)

            has_tool_calls = False
            final_output = None

            for item in response.output:
                if item.type == "message":
                    for content in item.content:
                        if content.type == "output_text":
                            final_output = content.text

                elif item.type == "function_call":
                    has_tool_calls = True
                    function_name = item.name
                    function_args = json.loads(item.arguments)

                    tools_used.append(function_name)

                    tool_result = self._execute_tool(
                        function_name, function_args, tool_map
                    )

                    self.client.responses.create(
                        model=self.model,
                        instructions=instructions,
                        input=[
                            {
                                "type": "function_call_output",
                                "call_id": item.id,
                                "output": json.dumps(tool_result),
                            }
                        ],
                        previous_response_id=previous_response_id,
                    )

            if not has_tool_calls and final_output:
                return {
                    "output": final_output,
                    "iterations": iteration,
                    "tools_used": tools_used,
                    "usage": {
                        "input_tokens": self.total_input_tokens,
                        "output_tokens": self.total_output_tokens,
                        "total_tokens": self.total_input_tokens
                        + self.total_output_tokens,
                    },
                }

        return {
            "output": final_output or "Maximum iterations reached",
            "iterations": iteration,
            "tools_used": tools_used,
            "usage": {
                "input_tokens": self.total_input_tokens,
                "output_tokens": self.total_output_tokens,
                "total_tokens": self.total_input_tokens + self.total_output_tokens,
            },
        }

    def _convert_tools_to_openai_format(
        self, tools: list[BaseTool]
    ) -> list[dict[str, Any]]:
        """
        Convert BaseTool instances to OpenAI tools format.

        Args:
            tools: List of tool instances

        Returns:
            List of tools in OpenAI Responses API format
        """
        openai_tools = []
        for tool in tools:
            openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
            )
        return openai_tools

    def _execute_tool(
        self, tool_name: str, args: dict[str, Any], tool_map: dict[str, BaseTool]
    ) -> Any:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool
            args: Tool arguments
            tool_map: Mapping of tool names to tool instances

        Returns:
            Tool execution result
        """
        if tool_name not in tool_map:
            return {"error": f"Tool {tool_name} not found"}

        tool = tool_map[tool_name]
        try:
            return tool.execute(args, {})
        except Exception as e:
            return {"error": str(e)}
