"""Tool for getting full product details from SQL database."""

from typing import Any

from custom_rag.core.base_tool import BaseTool
from custom_rag.pipelines.company_1.models import Product


class GetProductDetailsTool(BaseTool):
    """Get full information about products from SQL database."""

    @property
    def name(self) -> str:
        return "get_product_details"

    @property
    def description(self) -> str:
        return """Get complete information about specific products from the database.
        Returns all product fields including description, benefits, compliance, SLA, and technical specs.
        Use after semantic_search to get full details on matched products."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of product IDs to fetch details for (e.g., ['SAP-001', 'SAP-002'])",
                }
            },
            "required": ["product_ids"],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Get product details from SQL database.

        Args:
            args: Tool arguments with product_ids list
            context: Request context with db connection

        Returns:
            Dict with full product information
        """
        db = context.get("db")
        if not db:
            return {"error": "Database connection not available"}

        product_ids = args.get("product_ids", [])
        if not product_ids:
            return {"error": "No product IDs provided"}

        try:
            session = db.get_session()

            # Query products by IDs
            products_query = (
                session.query(Product).filter(Product.id.in_(product_ids)).all()
            )

            products = []
            for product in products_query:
                products.append(
                    {
                        "id": product.id,
                        "name": product.name,
                        "vendor": product.vendor,
                        "product_type": product.product_type,
                        "service_family": product.service_family,
                        "lifecycle_status": product.lifecycle_status,
                        "is_standard_portfolio": product.is_standard_portfolio,
                        "full_description": product.full_description,
                        "key_benefits": product.key_benefits,
                        "use_cases": product.use_cases,
                        "target_customer": product.target_customer,
                        "data_residency": product.data_residency,
                        "certifications": product.certifications,
                        "sla_support_hours": product.sla_support_hours,
                        "sla_response_critical": product.sla_response_critical,
                        "sla_uptime_guarantee": product.sla_uptime_guarantee,
                        "sla_included_services": product.sla_included_services,
                        "project_duration_min_weeks": product.project_duration_min_weeks,
                        "project_duration_max_weeks": product.project_duration_max_weeks,
                        "project_assumptions": product.project_assumptions,
                        "fulfillment_type": product.fulfillment_type,
                        "infrastructure_cloud_provider": product.infrastructure_cloud_provider,
                        "owner_team": product.owner_team,
                        "owner_email": product.owner_email,
                    }
                )

            session.close()

            return {
                "products": products,
                "total_found": len(products),
                "requested_count": len(product_ids),
            }

        except Exception as e:
            return {"error": f"Failed to get product details: {str(e)}"}
