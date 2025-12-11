import json
from unittest.mock import patch

import pytest
from django.test import RequestFactory

from custom_rag.utils import ErrorCodes
from custom_rag.views import execute_pipeline


class TestExecutePipeline:
    """Tests for execute_pipeline view."""

    @pytest.fixture
    def request_factory(self):
        """Provide a Django request factory."""
        return RequestFactory()

    @patch("custom_rag.views.registry.get_pipeline")
    def test_execute_pipeline_success(self, mock_get_pipeline, request_factory):
        """Test successful pipeline execution."""
        from unittest.mock import MagicMock

        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.execute.return_value = {
            "output": "Test output",
            "iterations": 5,
            "tools_used": ["tool1"],
            "usage": {
                "input_tokens": 100,
                "output_tokens": 200,
                "total_tokens": 300,
            },
        }

        mock_pipeline_class = MagicMock()
        mock_pipeline_class.return_value.__enter__.return_value = mock_pipeline_instance
        mock_pipeline_class.return_value.__exit__.return_value = None

        mock_get_pipeline.return_value = (mock_pipeline_class, {}, {})

        request_data = {
            "function_id": "test_pipeline",
            "llm_provider": "openai",
            "llm": "gpt-4o",
            "prompt_objects": {"query": "test"},
        }

        request = request_factory.post(
            "/custom_rag/execute/",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        response = execute_pipeline(request)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["success"] is True
        assert response_data["data"]["output"] == "Test output"
        assert response_data["usage"]["input_tokens"] == 100

    def test_execute_pipeline_missing_function_id(self, request_factory):
        """Test error when function_id is missing."""
        request = request_factory.post(
            "/custom_rag/execute/",
            data=json.dumps({"llm": "gpt-4o"}),
            content_type="application/json",
        )

        response = execute_pipeline(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data["success"] is False
        assert response_data["error"]["code"] == ErrorCodes.INVALID_REQUEST

    def test_execute_pipeline_invalid_json(self, request_factory):
        """Test error when JSON is invalid."""
        # Create request with invalid JSON by setting body directly
        request = request_factory.post(
            "/custom_rag/execute/",
            content_type="application/json",
        )
        # Set invalid JSON in the body
        request._body = b"invalid json"

        response = execute_pipeline(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data["success"] is False
        assert response_data["error"]["code"] == ErrorCodes.INVALID_JSON

    @patch("custom_rag.views.registry.get_pipeline")
    def test_execute_pipeline_not_found(self, mock_get_pipeline, request_factory):
        """Test error when pipeline is not found."""
        mock_get_pipeline.side_effect = ValueError("Pipeline 'nonexistent' not found")

        request_data = {
            "function_id": "nonexistent",
            "llm_provider": "openai",
            "llm": "gpt-4o",
        }

        request = request_factory.post(
            "/custom_rag/execute/",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        response = execute_pipeline(request)

        assert response.status_code == 404
        response_data = json.loads(response.content)
        assert response_data["error"]["code"] == ErrorCodes.PIPELINE_NOT_FOUND

    @patch("custom_rag.views.registry.get_pipeline")
    def test_execute_pipeline_internal_error(self, mock_get_pipeline, request_factory):
        """Test error handling for unexpected exceptions."""
        mock_get_pipeline.side_effect = Exception("Unexpected error")

        request_data = {
            "function_id": "test_pipeline",
            "llm_provider": "openai",
            "llm": "gpt-4o",
        }

        request = request_factory.post(
            "/custom_rag/execute/",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        response = execute_pipeline(request)

        assert response.status_code == 500
        response_data = json.loads(response.content)
        assert response_data["error"]["code"] == ErrorCodes.INTERNAL_ERROR
