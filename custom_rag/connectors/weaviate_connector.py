import os
from typing import Any

import weaviate
from weaviate.classes.query import Filter


class WeaviateConnector:
    """Wrapper for Weaviate client for vector search operations."""

    def __init__(self, collection_name: str):
        """
        Initialize Weaviate connection.

        Args:
            collection_name: Name of the Weaviate collection to use
        """
        self.collection_name = collection_name
        self.client: weaviate.WeaviateClient | None = None
        self.collection = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Weaviate."""
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

        # Determine if this is a cloud instance or local
        is_cloud = "weaviate.cloud" in weaviate_url or "weaviate.network" in weaviate_url

        if is_cloud:
            # For Weaviate Cloud, use connect_to_weaviate_cloud
            cluster_url = weaviate_url.replace("https://", "").replace("http://", "")
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=cluster_url,
                auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key),
            )
        else:
            # For local/custom Weaviate instances
            is_secure = weaviate_url.startswith("https://")
            host = weaviate_url.replace("http://", "").replace("https://", "")

            self.client = weaviate.connect_to_custom(
                http_host=host,
                http_port=443 if is_secure else 8080,
                http_secure=is_secure,
                grpc_host=host,
                grpc_port=443 if is_secure else 50051,
                grpc_secure=is_secure,
                auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key) if weaviate_api_key else None,
            )

        self.collection = self.client.collections.get(self.collection_name)

    def semantic_search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Perform semantic search on the collection.

        Args:
            query: Search query text
            filters: Optional filter criteria as dict
            top_k: Number of results to return

        Returns:
            List of search results with properties and metadata
        """
        search_query = self.collection.query.near_text(
            query=query,
            limit=top_k,
        )

        if filters:
            search_query = search_query.with_where(self._build_filter(filters))

        response = search_query.do()

        results = []
        for obj in response.objects:
            results.append(
                {
                    "id": str(obj.uuid),
                    "properties": obj.properties,
                    "metadata": {
                        "score": obj.metadata.score
                        if hasattr(obj.metadata, "score")
                        else None,
                        "distance": obj.metadata.distance
                        if hasattr(obj.metadata, "distance")
                        else None,
                    },
                }
            )

        return results

    def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """
        Retrieve objects by their IDs.

        Args:
            ids: List of object UUIDs

        Returns:
            List of objects with their properties
        """
        results = []
        for obj_id in ids:
            try:
                obj = self.collection.query.fetch_object_by_id(obj_id)
                if obj:
                    results.append(
                        {
                            "id": str(obj.uuid),
                            "properties": obj.properties,
                        }
                    )
            except Exception:
                continue

        return results

    def _build_filter(self, filters: dict[str, Any]) -> Filter:
        """
        Build Weaviate filter from dict.

        Args:
            filters: Filter criteria as dict

        Returns:
            Weaviate Filter object
        """
        filter_conditions = []
        for key, value in filters.items():
            filter_conditions.append(Filter.by_property(key).equal(value))

        if len(filter_conditions) == 1:
            return filter_conditions[0]

        result = filter_conditions[0]
        for condition in filter_conditions[1:]:
            result = result & condition

        return result

    def close(self) -> None:
        """Close Weaviate connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.collection = None
