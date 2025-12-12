from unittest.mock import MagicMock, Mock, patch

from custom_rag.connectors.database import DatabaseConnector
from custom_rag.connectors.weaviate_connector import WeaviateConnector


class TestDatabaseConnector:
    """Tests for DatabaseConnector."""

    @patch("custom_rag.connectors.database.create_engine")
    @patch("custom_rag.connectors.database.sessionmaker")
    def test_init_creates_engine(self, mock_sessionmaker, mock_create_engine):
        """Test that initializing creates an engine with correct parameters."""
        connection_string = "sqlite:///:memory:"
        connector = DatabaseConnector(connection_string)

        mock_create_engine.assert_called_once_with(
            connection_string,
            pool_pre_ping=True,
        )
        assert connector.engine is not None

    @patch("custom_rag.connectors.database.create_engine")
    @patch("custom_rag.connectors.database.sessionmaker")
    def test_get_session_returns_session(self, mock_sessionmaker, mock_create_engine):
        """Test that get_session returns a session."""
        mock_session = Mock()
        mock_sessionmaker.return_value = Mock(return_value=mock_session)

        connector = DatabaseConnector("sqlite:///:memory:")
        session = connector.get_session()

        assert session is not None

    @patch("custom_rag.connectors.database.create_engine")
    @patch("custom_rag.connectors.database.sessionmaker")
    def test_close_cleans_up_resources(self, mock_sessionmaker, mock_create_engine):
        """Test that close properly cleans up all resources."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        mock_session = Mock()
        mock_sessionmaker.return_value = Mock(return_value=mock_session)

        connector = DatabaseConnector("sqlite:///:memory:")
        connector.get_session()
        connector.close()

        mock_session.close.assert_called_once()
        mock_engine.dispose.assert_called_once()
        assert connector.engine is None


class TestWeaviateConnector:
    """Tests for WeaviateConnector."""

    @patch("custom_rag.connectors.weaviate_connector.weaviate.connect_to_custom")
    def test_init_connects_to_weaviate(self, mock_connect):
        """Test that initializing connects to Weaviate."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.collections.get.return_value = mock_collection
        mock_connect.return_value = mock_client

        connector = WeaviateConnector("TestCollection")

        assert connector.client is not None
        assert connector.collection is not None
        mock_client.collections.get.assert_called_once_with("TestCollection")

    @patch("custom_rag.connectors.weaviate_connector.weaviate.connect_to_custom")
    def test_semantic_search_returns_results(self, mock_connect):
        """Test that semantic_search returns formatted results."""
        mock_client = Mock()
        mock_collection = Mock()

        mock_obj = MagicMock()
        mock_obj.uuid = "test-uuid"
        mock_obj.properties = {"name": "Test Item"}
        mock_obj.metadata.score = 0.95
        mock_obj.metadata.distance = 0.05

        mock_response = Mock()
        mock_response.objects = [mock_obj]

        # Weaviate v4 API: near_text() returns response directly (no .do())
        mock_collection.query.near_text.return_value = mock_response

        mock_client.collections.get.return_value = mock_collection
        mock_connect.return_value = mock_client

        connector = WeaviateConnector("TestCollection")
        results = connector.semantic_search("test query", top_k=5)

        assert len(results) == 1
        assert results[0]["id"] == "test-uuid"
        assert results[0]["properties"]["name"] == "Test Item"
        assert results[0]["metadata"]["score"] == 0.95

    @patch("custom_rag.connectors.weaviate_connector.weaviate.connect_to_custom")
    def test_close_closes_client(self, mock_connect):
        """Test that close properly closes the client."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.collections.get.return_value = mock_collection
        mock_connect.return_value = mock_client

        connector = WeaviateConnector("TestCollection")
        connector.close()

        mock_client.close.assert_called_once()
        assert connector.client is None
