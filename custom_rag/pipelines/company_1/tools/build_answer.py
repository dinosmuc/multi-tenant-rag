"""Tool for progressively building the final answer during execution."""

import json
from typing import Any

from custom_rag.core.base_tool import BaseTool


class BuildAnswerTool(BaseTool):
    """Progressively build the final answer throughout execution."""

    @property
    def name(self) -> str:
        return "build_answer"

    @property
    def description(self) -> str:
        return """Store findings progressively as you work through your analysis.
        Call this tool IMMEDIATELY after each tool that produces significant findings.
        Do NOT wait until the end - build the answer section by section as you discover information.
        This ensures no information is lost and supports large responses."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "Which section to update: task_type, matched_requirements, unmatched_requirements, partial_matches, recommended_products, dependencies, pricing_summary, project_timeline, compliance_status, compatibility_check, warnings, alternatives, confidence_scores",
                },
                "action": {
                    "type": "string",
                    "enum": ["add", "update", "append"],
                    "description": "Action: 'add' (add item to list), 'update' (replace section), 'append' (merge with existing)",
                    "default": "add",
                },
                "data": {
                    "description": "The data to store in this section (can be object, array, or string)",
                },
                "notes": {
                    "type": "string",
                    "description": "Notes or text content for this section (alternative to data)",
                },
            },
            "required": ["section"],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Build or update the answer progressively.

        Args:
            args: Tool arguments with section, action, data, and notes
            context: Request context with answer_builder

        Returns:
            Confirmation with current answer status
        """
        # Initialize answer_builder if not exists
        if "answer_builder" not in context:
            context["answer_builder"] = self._initialize_answer_structure()

        answer_builder = context["answer_builder"]
        section = args.get("section")
        action = args.get("action", "add")

        # Use data if provided, otherwise use notes as the data
        data = args.get("data")
        notes = args.get("notes", "")
        if data is None and notes:
            data = notes

        # Validate that we have data to store
        if data is None:
            return {
                "error": "Either 'data' or 'notes' must be provided to store in the answer"
            }

        # Validate section
        valid_sections = [
            "task_type",
            "matched_requirements",
            "unmatched_requirements",
            "partial_matches",
            "recommended_products",
            "dependencies",
            "pricing_summary",
            "project_timeline",
            "compliance_status",
            "compatibility_check",
            "warnings",
            "alternatives",
            "confidence_scores",
        ]

        if section not in valid_sections:
            return {
                "error": f"Invalid section '{section}'. Valid sections: {', '.join(valid_sections)}"
            }

        # Perform action
        try:
            if action == "add":
                # Add to list
                if section not in answer_builder:
                    answer_builder[section] = []
                if isinstance(answer_builder[section], list):
                    answer_builder[section].append(data)
                else:
                    # If section is not a list, convert to update
                    answer_builder[section] = data

            elif action == "update":
                # Replace entire section
                answer_builder[section] = data

            elif action == "append":
                # Merge with existing
                if section not in answer_builder:
                    answer_builder[section] = data
                elif isinstance(answer_builder[section], list) and isinstance(
                    data, list
                ):
                    answer_builder[section].extend(data)
                elif isinstance(answer_builder[section], dict) and isinstance(
                    data, dict
                ):
                    answer_builder[section].update(data)
                else:
                    answer_builder[section] = data

            # Calculate current size
            answer_size = len(json.dumps(answer_builder))
            size_kb = round(answer_size / 1024, 2)

            # Get completed sections
            completed_sections = [k for k, v in answer_builder.items() if v]

            return {
                "success": True,
                "message": f"Updated '{section}' section",
                "action_performed": action,
                "current_answer_size_kb": size_kb,
                "sections_completed": completed_sections,
                "total_sections": len(completed_sections),
                "notes": notes if notes else None,
            }

        except Exception as e:
            return {"error": f"Failed to build answer: {str(e)}"}

    def _initialize_answer_structure(self) -> dict[str, Any]:
        """Initialize the answer structure with empty sections."""
        return {
            "task_type": None,
            "matched_requirements": [],
            "unmatched_requirements": [],
            "partial_matches": [],
            "recommended_products": [],
            "dependencies": [],
            "pricing_summary": {},
            "project_timeline": {},
            "compliance_status": {},
            "compatibility_check": {},
            "warnings": [],
            "alternatives": [],
            "confidence_scores": {},
        }
