import os
from abc import ABC, abstractmethod
from typing import Any

from custom_rag.connectors.database import DatabaseConnector
from custom_rag.connectors.weaviate_connector import WeaviateConnector
from custom_rag.core.base_tool import BaseTool


class BasePipeline(ABC):
    """Abstract base class for all RAG pipelines."""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize pipeline with configuration.

        Args:
            config: Pipeline configuration from pipelines.json
        """
        self.config = config
        self.db: DatabaseConnector | None = None
        self.weaviate: WeaviateConnector | None = None
        self.tools: list[BaseTool] = []

    def __enter__(self):
        """
        Initialize connections and resources.

        Returns:
            Self for context manager pattern
        """
        db_env_var = self.config.get("db_env_var")
        if db_env_var:
            db_url = os.getenv(db_env_var)
            if db_url:
                self.db = DatabaseConnector(db_url)

        weaviate_collection = self.config.get("weaviate_collection")
        if weaviate_collection:
            self.weaviate = WeaviateConnector(weaviate_collection)

        self.tools = self.get_tools()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Cleanup all resources.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if self.db:
            self.db.close()
            self.db = None

        if self.weaviate:
            self.weaviate.close()
            self.weaviate = None

        self.tools = []

    @abstractmethod
    def get_tools(self) -> list[BaseTool]:
        """
        Return list of tool instances for this pipeline.

        Returns:
            List of instantiated tools
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Return system prompt for the LLM agent.

        Returns:
            System prompt string
        """
        pass

    @abstractmethod
    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the pipeline.

        Args:
            context: Request context containing user data

        Returns:
            Pipeline execution result
        """
        pass
