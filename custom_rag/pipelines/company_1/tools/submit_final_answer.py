"""Tool for finalizing and submitting the complete answer."""

from typing import Any

from custom_rag.core.base_tool import BaseTool


class SubmitFinalAnswerTool(BaseTool):
    """Submit the final answer and break the agentic loop."""

    @property
    def name(self) -> str:
        return "submit_final_answer"

    @property
    def description(self) -> str:
        return """Call this tool when you have completed your analysis and built the complete answer.
        This is THE ONLY WAY to finish the task and return results to the user.

        Only call this when:
        1. You have addressed ALL customer requirements
        2. You have built a complete answer using build_answer tool
        3. Your goal is fully achieved
        4. You are 100% confident in the completeness and accuracy of your response

        Do NOT call this prematurely - ensure all analysis is complete first."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Brief summary of what you accomplished (e.g., 'Found 3 compliant products, calculated 3-year TCO of 450K CHF, within customer budget')",
                },
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Your confidence level in the completeness of this answer",
                    "default": "high",
                },
            },
            "required": ["summary"],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Finalize and return the complete answer.

        This will cause the agent loop to break and return the answer to the user.

        Args:
            args: Tool arguments with summary and confidence
            context: Request context with answer_builder

        Returns:
            The complete final answer (triggers loop break)
        """
        summary = args.get("summary", "")
        confidence = args.get("confidence", "high")
        answer_builder = context.get("answer_builder", {})

        if not answer_builder or not any(answer_builder.values()):
            return {
                "error": "Cannot submit final answer: No answer has been built yet. Use build_answer tool first to construct your response."
            }

        # Mark answer as completed
        answer_builder["_status"] = "completed"
        answer_builder["_summary"] = summary
        answer_builder["_confidence"] = confidence

        # Count non-empty sections
        non_empty_sections = sum(1 for v in answer_builder.values() if v)

        # Return the complete answer
        # This will be detected by OpenAIProvider as final output and break the loop
        return {
            "status": "completed",
            "summary": summary,
            "confidence": confidence,
            "sections_completed": non_empty_sections,
            "message": f"Analysis complete. Returning {non_empty_sections} sections to user.",
            "final_answer": answer_builder,
        }
