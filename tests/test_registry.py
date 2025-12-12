from unittest.mock import Mock, mock_open, patch

import pytest

from custom_rag.core.openai_provider import OpenAIProvider
from custom_rag.registry import PipelineRegistry


class TestPipelineRegistry:
    """Tests for PipelineRegistry."""

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"test_pipeline": {"pipeline": "test.module.TestPipeline", "config": {}}}',
    )
    def test_load_config_loads_pipelines(self, mock_file):
        """Test that load_config properly loads pipelines from JSON."""
        registry = PipelineRegistry()
        assert "test_pipeline" in registry.pipelines

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"test": {"pipeline": "test.Pipeline", "config": {}}}',
    )
    def test_get_pipeline_returns_class_and_config(self, mock_file):
        """Test that get_pipeline returns pipeline class, config, and context."""
        with patch.object(PipelineRegistry, "_import_pipeline_class") as mock_import:
            mock_class = Mock()
            mock_import.return_value = mock_class

            registry = PipelineRegistry()
            request_data = {
                "llm": "gpt-4o",
                "llm_provider": "openai",
                "prompt_objects": {},
            }

            pipeline_class, config, context = registry.get_pipeline(
                "test", request_data
            )

            assert pipeline_class == mock_class
            assert isinstance(config, dict)
            assert context["llm"] == "gpt-4o"
            assert isinstance(context["llm_provider"], OpenAIProvider)
            assert context["llm_provider"].model == "gpt-4o"

    @patch("builtins.open", new_callable=mock_open, read_data="{}")
    def test_get_pipeline_raises_error_if_not_found(self, mock_file):
        """Test that get_pipeline raises ValueError if pipeline not found."""
        registry = PipelineRegistry()

        with pytest.raises(ValueError, match="not found"):
            registry.get_pipeline("nonexistent", {})

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"test": {"pipeline": "test.Pipeline", "config": {}}}',
    )
    def test_build_context_requires_llm(self, mock_file):
        """Test that _build_context raises error if llm is missing."""
        registry = PipelineRegistry()

        with pytest.raises(ValueError, match="'llm' model must be provided"):
            registry._build_context({"llm_provider": "openai"})

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"test": {"pipeline": "test.Pipeline", "config": {}}}',
    )
    def test_build_context_requires_llm_provider(self, mock_file):
        """Test that _build_context raises error if llm_provider is missing."""
        registry = PipelineRegistry()

        with pytest.raises(ValueError, match="'llm_provider' must be provided"):
            registry._build_context({"llm": "gpt-4o"})

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"test": {"pipeline": "test.Pipeline", "config": {}}}',
    )
    def test_build_context_includes_reasoning_effort(self, mock_file):
        """Test that _build_context includes reasoning_effort if provided."""
        registry = PipelineRegistry()

        context = registry._build_context(
            {
                "llm": "o3",
                "llm_provider": "openai",
                "reasoning_effort": "high",
            }
        )

        assert context["reasoning_effort"] == "high"

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"test": {"pipeline": "test.Pipeline", "config": {}}}',
    )
    def test_build_context_reasoning_effort_optional(self, mock_file):
        """Test that reasoning_effort is optional."""
        registry = PipelineRegistry()

        context = registry._build_context(
            {
                "llm": "gpt-4o",
                "llm_provider": "openai",
            }
        )

        assert context["reasoning_effort"] is None
