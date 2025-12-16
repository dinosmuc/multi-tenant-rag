from unittest.mock import MagicMock, Mock

import pytest


def pytest_ignore_collect(path, config):  # noqa: ARG001
    """
    Exclude `test_cases.py` from normal pytest runs.

    That module is an expensive end-to-end evaluation harness that can require
    live OpenAI/DB/Weaviate access. Run it manually as a standalone script:
    `python tests/test_cases.py ...`

    If you *really* want pytest to collect it, set `RUN_RAG_EVAL_TESTS=1`.
    """
    import os

    if os.getenv("RUN_RAG_EVAL_TESTS") == "1":
        return False

    filename = getattr(path, "basename", None)  # pytest <8 uses py.path
    if filename is None:
        filename = getattr(path, "name", "")

    return filename == "test_cases.py"


@pytest.fixture
def mock_database_url():
    """Provide a mock database URL for testing."""
    return "sqlite:///:memory:"


@pytest.fixture
def mock_weaviate_client():
    """Provide a mock Weaviate client."""
    client = Mock()
    collection = Mock()
    client.collections.get.return_value = collection
    return client


@pytest.fixture
def mock_openai_client():
    """Provide a mock OpenAI client."""
    client = Mock()
    response = MagicMock()
    response.id = "resp_123"
    response.output = [
        MagicMock(
            type="message",
            content=[MagicMock(type="output_text", text="Test response")],
        )
    ]
    response.usage = MagicMock(input_tokens=10, output_tokens=20)
    client.responses.create.return_value = response
    return client


@pytest.fixture
def sample_request_data():
    """Provide sample request data for testing."""
    return {
        "function_id": "test_pipeline",
        "llm_provider": "openai",
        "llm": "gpt-4o",
        "reasoning_effort": "medium",
        "prompt_objects": {"query": "Test query"},
        "scope_variables": {},
        "previous_prompt_outputs": {},
    }


@pytest.fixture
def sample_pipeline_config():
    """Provide sample pipeline configuration."""
    return {
        "weaviate_collection": "TestCollection",
        "db_env_var": "TEST_DB_URL",
        "max_iterations": 10,
    }


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("WEAVIATE_URL", "http://localhost:8080")
    monkeypatch.setenv("WEAVIATE_API_KEY", "test-weaviate-key")
    monkeypatch.setenv("TEST_DB_URL", "sqlite:///:memory:")
