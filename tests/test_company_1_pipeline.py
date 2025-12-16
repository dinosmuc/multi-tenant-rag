"""Tests for Company_1 pipeline."""

from unittest.mock import Mock, patch

import pytest

from custom_rag.pipelines.company_1.pipeline import Company1Pipeline
from custom_rag.pipelines.company_1.tools.create_final_answer import (
    CreateFinalAnswerTool,
)
from custom_rag.pipelines.company_1.tools.semantic_search import SemanticSearchTool


class TestCompany1Pipeline:
    """Basic tests for Company_1 pipeline."""

    def test_pipeline_can_be_instantiated(self):
        """Test that pipeline can be created."""
        config = {
            "weaviate_collection": "Company1Products",
            "db_env_var": "COMPANY_1_DB_URL",
            "max_iterations": 100,
        }
        pipeline = Company1Pipeline(config)
        assert pipeline is not None
        assert pipeline.config == config

    def test_pipeline_has_8_tools(self):
        """Test that pipeline provides all 8 tools."""
        config = {"weaviate_collection": "Company1Products"}
        pipeline = Company1Pipeline(config)
        tools = pipeline.get_tools()

        assert len(tools) == 8
        tool_names = [tool.name for tool in tools]
        assert "semantic_search" in tool_names
        assert "get_product_details" in tool_names
        assert "get_pricing" in tool_names
        assert "get_dependencies" in tool_names
        assert "get_project_phases" in tool_names
        assert "check_compatibility" in tool_names
        assert "get_compliance_info" in tool_names
        assert "create_final_answer" in tool_names

    def test_pipeline_has_system_prompt(self):
        """Test that pipeline provides system prompt."""
        config = {"weaviate_collection": "Company1Products"}
        pipeline = Company1Pipeline(config)
        prompt = pipeline.get_system_prompt()

        assert prompt is not None
        assert len(prompt) > 1000  # Should be comprehensive
        assert "Company_1" in prompt
        assert "DATABASE SCHEMAS" in prompt
        assert "COMPLETING THE TASK" in prompt
        assert "TOOL USAGE GUIDELINES" in prompt

    @patch("custom_rag.pipelines.company_1.pipeline.AgentExecutor")
    def test_pipeline_execute_injects_connections_and_returns_output(
        self, mock_executor_class
    ):
        """Test that execute injects db/weaviate into context and returns output."""
        config = {"weaviate_collection": "Company1Products", "max_iterations": 100}
        pipeline = Company1Pipeline(config)
        pipeline.db = Mock()
        pipeline.weaviate = Mock()

        # Mock the executor
        mock_executor = Mock()
        mock_executor.execute.return_value = {
            "output": "test output",
            "iterations": 5,
            "tools_used": ["semantic_search"],
        }
        mock_executor_class.return_value = mock_executor

        # Mock LLM provider
        mock_provider = Mock()

        context = {
            "llm_provider": mock_provider,
            "prompt_objects": {"query": "test query"},
        }

        # Execute
        result = pipeline.execute(context)

        assert context["db"] is pipeline.db
        assert context["weaviate"] is pipeline.weaviate

        # Check result
        assert result["output"] == "test output"
        assert "iterations" in result
        assert "tools_used" in result


class TestSemanticSearchTool:
    """Test semantic search tool."""

    def test_tool_has_correct_name(self):
        """Test tool name."""
        tool = SemanticSearchTool()
        assert tool.name == "semantic_search"

    def test_tool_has_description(self):
        """Test tool has description."""
        tool = SemanticSearchTool()
        assert tool.description is not None
        assert len(tool.description) > 50

    def test_tool_has_parameters_schema(self):
        """Test tool has JSON schema."""
        tool = SemanticSearchTool()
        params = tool.parameters

        assert params["type"] == "object"
        assert "query" in params["properties"]
        assert "query" in params["required"]

    def test_execute_returns_error_without_weaviate(self):
        """Test tool returns error when Weaviate not in context."""
        tool = SemanticSearchTool()
        result = tool.execute({"query": "test"}, {})

        assert "error" in result
        assert "Weaviate" in result["error"]

    def test_execute_with_mock_weaviate(self):
        """Test tool executes with mocked Weaviate."""
        tool = SemanticSearchTool()

        # Mock Weaviate
        mock_weaviate = Mock()
        mock_weaviate.semantic_search.return_value = [
            {
                "properties": {
                    "product_id": "SAP-001",
                    "name": "SAP S/4HANA",
                    "service_family": "SAP",
                },
                "metadata": {"score": 0.92},
            }
        ]

        context = {"weaviate": mock_weaviate}
        result = tool.execute({"query": "SAP migration"}, context)

        assert "products" in result
        assert len(result["products"]) == 1
        assert result["products"][0]["product_id"] == "SAP-001"
        assert result["products"][0]["relevance"] == "high"


class TestCreateFinalAnswerTool:
    """Tests for create_final_answer tool."""

    def test_tool_has_correct_name(self):
        """Test tool name."""
        tool = CreateFinalAnswerTool()
        assert tool.name == "create_final_answer"

    def test_execute_rejects_empty_answer(self):
        """Test tool rejects empty answers."""
        tool = CreateFinalAnswerTool()

        result = tool.execute({"answer": "   "}, {})
        assert "error" in result

    def test_execute_stores_final_answer_in_context(self):
        """Test tool stores final_answer in the context for the pipeline to return."""
        tool = CreateFinalAnswerTool()
        context = {}

        result = tool.execute({"answer": "Final response"}, context)

        assert result["status"] == "completed"
        assert context["final_answer"] == "Final response"
        assert context["_task_completed"] is True


class TestToolsReceiveContext:
    """Test that tools properly receive context with db and weaviate."""

    def test_tools_can_access_db_from_context(self):
        """Test tools can access database connection from context."""
        from custom_rag.pipelines.company_1.tools.get_product_details import (
            GetProductDetailsTool,
        )

        tool = GetProductDetailsTool()

        # Context without db
        result = tool.execute({"product_ids": ["SAP-001"]}, {})
        assert "error" in result
        assert "Database" in result["error"]

        # Context with mock db
        mock_db = Mock()
        context = {"db": mock_db}
        result = tool.execute({"product_ids": ["SAP-001"]}, context)
        # Will fail on query but proves db was accessed
        mock_db.get_session.assert_called_once()

    def test_tools_can_access_weaviate_from_context(self):
        """Test tools can access Weaviate from context."""
        tool = SemanticSearchTool()

        # Context without weaviate
        result = tool.execute({"query": "test"}, {})
        assert "error" in result
        assert "Weaviate" in result["error"]

        # Context with mock weaviate
        mock_weaviate = Mock()
        mock_weaviate.semantic_search.return_value = []
        context = {"weaviate": mock_weaviate}

        result = tool.execute({"query": "test"}, context)
        mock_weaviate.semantic_search.assert_called_once()
        assert "products" in result


@pytest.mark.integration
class TestPipelineIntegration:
    """Integration tests (require actual connections - mark with @pytest.mark.integration)."""

    @patch.dict("os.environ", {"COMPANY_1_DB_URL": "sqlite:///:memory:"})
    @patch("custom_rag.core.base_pipeline.WeaviateConnector")
    def test_pipeline_can_connect_to_database(self, mock_weaviate_connector):
        """Test pipeline can create database connection."""
        # Mock Weaviate connector to avoid connection issues
        mock_weaviate_instance = Mock()
        mock_weaviate_connector.return_value = mock_weaviate_instance

        config = {
            "db_env_var": "COMPANY_1_DB_URL",
            "weaviate_collection": "Company1Products",
        }

        pipeline = Company1Pipeline(config)

        # Use context manager to test connection
        with pipeline:
            assert pipeline.db is not None

        # Connection should be closed after exit
        assert pipeline.db is None
