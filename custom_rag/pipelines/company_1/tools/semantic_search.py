"""Semantic search tool for finding products matching customer requirements."""

from typing import Any

from custom_rag.core.base_tool import BaseTool


class SemanticSearchTool(BaseTool):
    """Find products matching customer requirements using semantic search."""

    @property
    def name(self) -> str:
        return "semantic_search"

    @property
    def description(self) -> str:
        return """Search for products matching customer requirements using semantic similarity.
        Use this for initial product discovery based on natural language descriptions.
        Returns ranked products with relevance scores."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query describing what customer needs (e.g., 'SAP S/4HANA migration for 200 users')",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default 10, max 50)",
                    "default": 10,
                },
                "filters": {
                    "type": "object",
                    "description": "Optional filters to narrow search",
                    "properties": {
                        "service_family": {
                            "type": "string",
                            "description": "Filter by service family: SAP, Cloud, Workplace, Security, Network, Consulting",
                        },
                        "product_type": {
                            "type": "string",
                            "description": "Filter by type: Projekt, SLA, Handelsware, Lizenz",
                        },
                        "lifecycle_status": {
                            "type": "string",
                            "description": "Filter by status: Active, Preview, Deprecated, EndOfSale",
                        },
                    },
                },
            },
            "required": ["query"],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Execute semantic search in Weaviate.

        Args:
            args: Tool arguments with query, top_k, and optional filters
            context: Request context with weaviate connection

        Returns:
            Dict with found products and their relevance scores
        """
        weaviate = context.get("weaviate")
        if not weaviate:
            return {"error": "Weaviate connection not available"}

        query = args.get("query")
        top_k = args.get("top_k", 10)
        filters_dict = args.get("filters", {})

        # Build Weaviate filters if provided
        weaviate_filters = None
        if filters_dict:
            weaviate_filters = {}
            for key, value in filters_dict.items():
                if value:
                    weaviate_filters[key] = value

        try:
            # Perform semantic search
            results = weaviate.semantic_search(
                query=query, filters=weaviate_filters, top_k=min(top_k, 50)
            )

            # Format results
            products = []
            for result in results:
                product_data = result.get("properties", {})
                metadata = result.get("metadata", {})

                # Get score or convert distance to score
                # Weaviate v4 near_text returns distance (0 = identical, higher = less similar)
                # Convert distance to score: score = 1 - distance (clamped to 0-1)
                score = metadata.get("score")
                distance = metadata.get("distance")

                if score is not None:
                    similarity = float(score)
                elif distance is not None:
                    # Convert distance to similarity score (cosine distance is typically 0-2)
                    similarity = max(0.0, 1.0 - float(distance))
                else:
                    similarity = 0.0

                # Determine relevance level based on similarity
                if similarity >= 0.85:
                    relevance = "high"
                elif similarity >= 0.70:
                    relevance = "medium"
                else:
                    relevance = "low"

                products.append(
                    {
                        "product_id": product_data.get("product_id"),
                        "name": product_data.get("name"),
                        "score": round(similarity, 3),
                        "relevance": relevance,
                        "description": product_data.get("description", ""),
                        "service_family": product_data.get("service_family"),
                        "product_type": product_data.get("product_type"),
                    }
                )

            return {
                "products": products,
                "total_found": len(products),
                "query": query,
                "filters_applied": filters_dict if filters_dict else None,
            }

        except Exception as e:
            return {"error": f"Semantic search failed: {str(e)}"}
