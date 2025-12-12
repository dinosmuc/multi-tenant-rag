import json
import logging
import os
from typing import Any

from openai import OpenAI

from custom_rag.core.base_tool import BaseTool
from custom_rag.core.llm_provider import LLMProvider

logger = logging.getLogger(__name__)


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
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute agentic loop using OpenAI Responses API.

        Args:
            instructions: System instructions
            user_message: User's message
            tools: Available tools
            max_iterations: Maximum iterations
            context: Request context with db, weaviate, and other resources

        Returns:
            Dict with output, iterations, and tools_used
        """
        if context is None:
            context = {}

        tool_map = {tool.name: tool for tool in tools}
        tools_used = []
        iteration = 0

        openai_tools = self._convert_tools_to_openai_format(tools)

        # Build up conversation history as input list
        input_list = []

        logger.info("=" * 80)
        logger.info("🚀 Starting agentic loop")
        logger.info(f"📝 User query: {user_message}")
        logger.info(f"🔧 Available tools: {', '.join(tool_map.keys())}")
        logger.info(f"🔄 Max iterations: {max_iterations}")
        logger.info("=" * 80)

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"\n{'='*80}")
            logger.info(f"🔄 ITERATION {iteration}/{max_iterations}")
            logger.info(f"{'='*80}")

            # On first iteration, use user message as string
            # On subsequent iterations, use accumulated input_list
            if iteration == 1:
                input_data = user_message
            else:
                input_data = input_list if input_list else user_message

            request_params = {
                "model": self.model,
                "instructions": instructions,
                "input": input_data,
                "tools": openai_tools,
            }

            if self.reasoning_effort:
                request_params["reasoning"] = {"effort": self.reasoning_effort}

            logger.info(f"📡 API Request params:")
            logger.info(f"  - model: {request_params.get('model')}")
            logger.info(f"  - input_type: {type(input_data).__name__}")
            logger.info(f"  - input_length: {len(input_data) if isinstance(input_data, list) else len(str(input_data))}")
            logger.info(f"  - tools_count: {len(openai_tools) if openai_tools else 0}")

            response = self.client.responses.create(**request_params)

            # Add response output to input list for next iteration
            if hasattr(response, 'output'):
                input_list += response.output
                logger.info(f"📝 Added {len(response.output)} items to input list (total: {len(input_list)})")

            if hasattr(response, "usage") and response.usage:
                self.total_input_tokens += getattr(response.usage, "input_tokens", 0)
                self.total_output_tokens += getattr(response.usage, "output_tokens", 0)

            has_tool_calls = False
            final_output = None
            tool_outputs = []

            # Process all items in the response
            for item in response.output:
                if item.type == "message":
                    for content in item.content:
                        if content.type == "output_text":
                            final_output = content.text
                            logger.info(f"💬 Agent response: {final_output[:200]}...")

                elif item.type == "function_call":
                    has_tool_calls = True
                    function_name = item.name
                    function_args = json.loads(item.arguments)

                    logger.info(f"\n🔧 Tool Call: {function_name}")
                    logger.info(f"📥 Arguments: {json.dumps(function_args, indent=2)}")

                    tools_used.append(function_name)

                    tool_result = self._execute_tool(
                        function_name, function_args, tool_map, context
                    )

                    # Log tool result (truncate if too long)
                    result_str = json.dumps(tool_result, indent=2)
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "... (truncated)"
                    logger.info(f"📤 Tool Result: {result_str}")

                    # Collect tool output for batch submission
                    tool_outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(tool_result),
                        }
                    )

            # Add tool outputs to input list for next iteration
            if tool_outputs:
                logger.info(f"📤 Adding {len(tool_outputs)} tool output(s) to input list...")
                input_list.extend(tool_outputs)
                logger.info(f"✅ Tool outputs added (input_list now has {len(input_list)} items)")
                # Continue to next iteration to send tool outputs back to model
                continue

            if not has_tool_calls and final_output:
                logger.info(f"\n{'='*80}")
                logger.info("✅ Loop completed: Agent returned final output")
                logger.info(f"📊 Total iterations: {iteration}")
                logger.info(f"🔧 Tools used: {', '.join(set(tools_used))}")
                logger.info(
                    f"📈 Token usage: {self.total_input_tokens} in / {self.total_output_tokens} out"
                )
                logger.info(f"{'='*80}\n")

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

        logger.warning(f"\n{'='*80}")
        logger.warning(f"⚠️  Maximum iterations reached ({max_iterations})")
        logger.warning(f"🔧 Tools used: {', '.join(set(tools_used))}")
        logger.warning(f"{'='*80}\n")

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
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            )
        return openai_tools

    def _execute_tool(
        self,
        tool_name: str,
        args: dict[str, Any],
        tool_map: dict[str, BaseTool],
        context: dict[str, Any],
    ) -> Any:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool
            args: Tool arguments
            tool_map: Mapping of tool names to tool instances
            context: Request context with db, weaviate, and other resources

        Returns:
            Tool execution result
        """
        if tool_name not in tool_map:
            return {"error": f"Tool {tool_name} not found"}

        tool = tool_map[tool_name]
        try:
            return tool.execute(args, context)
        except Exception as e:
            return {"error": str(e)}
