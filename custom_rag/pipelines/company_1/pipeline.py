"""Company_1 product catalog RAG pipeline implementation."""

import logging
from typing import Any

from custom_rag.core.agent_executor import AgentExecutor
from custom_rag.core.base_pipeline import BasePipeline
from custom_rag.core.base_tool import BaseTool
from custom_rag.pipelines.company_1.prompts.planning_prompt import PLANNING_PROMPT
from custom_rag.pipelines.company_1.prompts.system_prompt import SYSTEM_PROMPT
from custom_rag.pipelines.company_1.tools.check_compatibility import (
    CheckCompatibilityTool,
)
from custom_rag.pipelines.company_1.tools.create_final_answer import (
    CreateFinalAnswerTool,
)
from custom_rag.pipelines.company_1.tools.filter_by_compliance import (
    FilterByComplianceTool,
)
from custom_rag.pipelines.company_1.tools.get_dependencies import GetDependenciesTool
from custom_rag.pipelines.company_1.tools.get_pricing import GetPricingTool
from custom_rag.pipelines.company_1.tools.get_product_details import (
    GetProductDetailsTool,
)
from custom_rag.pipelines.company_1.tools.get_project_phases import GetProjectPhasesTool
from custom_rag.pipelines.company_1.tools.semantic_search import SemanticSearchTool

logger = logging.getLogger(__name__)


class Company1Pipeline(BasePipeline):
    """
    Company_1 product catalog RAG pipeline.

    Analyzes customer requirements against Company_1's catalog of 100 SAP/Cloud products.
    Supports three main task types:
    - Gap Analysis: Match requirements against available products
    - Solution Design: Build complete solutions with dependencies
    - Pricing: Calculate costs and TCO
    """

    def get_tools(self) -> list[BaseTool]:
        """
        Return all available tools for this pipeline.

        Returns:
            List of 8 tool instances
        """
        return [
            SemanticSearchTool(),
            GetProductDetailsTool(),
            GetPricingTool(),
            GetDependenciesTool(),
            GetProjectPhasesTool(),
            CheckCompatibilityTool(),
            FilterByComplianceTool(),
            CreateFinalAnswerTool(),
        ]

    def get_system_prompt(self) -> str:
        """
        Return system prompt with DB schemas and instructions.

        Returns:
            Complete system prompt string
        """
        return SYSTEM_PROMPT

    def get_planning_prompt(self) -> str:
        """
        Return planning prompt with execution planning instructions.

        Returns:
            Complete planning prompt string
        """
        return PLANNING_PROMPT

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the pipeline with agentic loop.

        Args:
            context: Request context containing:
                - prompt_objects: User input with 'query' field
                - llm_provider: LLM provider instance
                - db: Database connection (set by BasePipeline)
                - weaviate: Weaviate connection (set by BasePipeline)

        Returns:
            Dict with output, iterations, and tools_used
        """
        query = context.get("prompt_objects", {}).get("query", "")

        logger.info("\n" + "=" * 100)
        logger.info("🎯 COMPANY_1 PIPELINE STARTED")
        logger.info("=" * 100)
        logger.info(f"📝 Query: {query}")
        logger.info(f"🗄️  Database: {'Connected' if self.db else 'Not connected'}")
        logger.info(f"🔍 Weaviate: {'Connected' if self.weaviate else 'Not connected'}")
        logger.info(f"🤖 LLM: {context.get('llm_provider', 'Unknown')}")
        logger.info("=" * 100 + "\n")

        # Add db and weaviate connections to context
        context["db"] = self.db
        context["weaviate"] = self.weaviate

        # Get LLM provider from context
        llm_provider = context.get("llm_provider")
        if not llm_provider:
            logger.error("LLM provider not available in context")
            return {
                "output": {"error": "LLM provider not available in context"},
                "iterations": 0,
                "tools_used": [],
            }

        # Create agent executor
        agent_executor = AgentExecutor(
            tools=self.tools,
            system_prompt=self.get_system_prompt(),
            planning_prompt=self.get_planning_prompt(),
            llm_provider=llm_provider,
            max_iterations=self.config.get("max_iterations", 100),
        )

        # Execute agentic loop
        logger.info("Starting agent executor...")
        result = agent_executor.execute(context)

        # Get the final answer from context (set by create_final_answer tool)
        # or fall back to the raw output from the agent
        final_answer = context.get("final_answer")
        if final_answer:
            output = final_answer
            logger.info("Using final answer from create_final_answer tool")
        else:
            output = result.get("output", "No output generated")
            logger.info("Using raw output (no final answer created)")

        logger.info("\n" + "=" * 100)
        logger.info("✅ COMPANY_1 PIPELINE COMPLETED")
        logger.info(f"📊 Iterations used: {result.get('iterations', 0)}")
        logger.info(f"🔧 Total tool calls: {len(result.get('tools_used', []))}")
        logger.info("=" * 100 + "\n")

        return {
            "output": output,
            "iterations": result.get("iterations", 0),
            "tools_used": result.get("tools_used", []),
            "usage": result.get("usage", {}),
        }
