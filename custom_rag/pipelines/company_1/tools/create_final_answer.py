"""Tool for creating and returning the final answer to the user."""

from typing import Any

from custom_rag.core.base_tool import BaseTool


class CreateFinalAnswerTool(BaseTool):
    """Create the final answer and complete the task."""

    @property
    def name(self) -> str:
        return "create_final_answer"

    @property
    def description(self) -> str:
        return """Call this tool when you have gathered all necessary information and are ready to provide the final answer to the user.

        This is THE ONLY WAY to finish the task and return results to the user.

        Write a complete, well-structured answer that directly addresses the user's query.
        Include all relevant findings from your research (products found, pricing, dependencies, etc.).

        Only call this when:
        1. You have addressed the customer's requirements
        2. You have gathered all relevant information using other tools
        3. You are ready to provide a complete answer

        The answer you provide will be returned directly to the user."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "The complete final answer to return to the user. Include all relevant findings, recommendations, pricing information, and any other details that address the user's query.",
                },
            },
            "required": ["answer"],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Create and return the final answer.

        This will cause the agent loop to break and return the answer to the user.

        Args:
            args: Tool arguments with the answer
            context: Request context

        Returns:
            Success confirmation with the final answer
        """
        answer = args.get("answer", "")

        if not answer or not answer.strip():
            return {
                "error": "Cannot create final answer: The answer cannot be empty. Please provide a complete answer."
            }

        # Store the final answer in context for the pipeline to retrieve
        context["final_answer"] = answer
        context["_task_completed"] = True

        return {
            "status": "completed",
            "message": "Final answer created successfully. Returning to user.",
            "answer_length": len(answer),
        }
