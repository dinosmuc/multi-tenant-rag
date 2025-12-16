"""Tool for retrieving compliance information for products."""

from typing import Any

from custom_rag.core.base_tool import BaseTool
from custom_rag.pipelines.company_1.models import Product


class FilterByComplianceTool(BaseTool):
    """Retrieve compliance and regulatory information for products."""

    @property
    def name(self) -> str:
        return "get_compliance_info"

    @property
    def description(self) -> str:
        return """Retrieve compliance and regulatory information for products.

        Returns for each product:
        - certifications: Array of certifications (ISO 27001, SOC 2, FINMA, SAP Certified, etc.)
        - data_residency: Where data is stored (Switzerland, EU, Global, Customer_Choice)
        - sla_uptime_guarantee: Uptime guarantee percentage
        - sla_support_hours: Support availability (24x7, Business_Hours, etc.)

        Use this to check if products meet compliance requirements.
        YOU must match the returned data against the user's requirements."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of product IDs to get compliance info for. Leave empty to get all products.",
                },
            },
            "required": [],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Retrieve compliance information for products.

        Args:
            args: Tool arguments with optional product_ids
            context: Request context with db connection

        Returns:
            Dict with compliance data for each product
        """
        db = context.get("db")
        if not db:
            return {"error": "Database connection not available"}

        product_ids = args.get("product_ids", [])

        try:
            session = db.get_session()

            # Build query
            query = session.query(Product)
            if product_ids:
                query = query.filter(Product.id.in_(product_ids))

            # Only get active products if no specific IDs provided
            if not product_ids:
                query = query.filter(Product.lifecycle_status == "Active")

            products = query.all()

            # Build compliance data for each product
            compliance_data = []
            for product in products:
                product_compliance = {
                    "product_id": product.id,
                    "product_name": product.name,
                    "service_family": product.service_family,
                    "certifications": product.certifications or [],
                    "data_residency": product.data_residency,
                    "sla_uptime_guarantee": product.sla_uptime_guarantee,
                    "sla_support_hours": product.sla_support_hours,
                    "sla_response_critical": product.sla_response_critical,
                    "lifecycle_status": product.lifecycle_status,
                }
                compliance_data.append(product_compliance)

            session.close()

            # Get unique values for reference
            all_certifications = set()
            all_data_residencies = set()
            for p in compliance_data:
                if p["certifications"]:
                    all_certifications.update(p["certifications"])
                if p["data_residency"]:
                    all_data_residencies.add(p["data_residency"])

            return {
                "products": compliance_data,
                "total_products": len(compliance_data),
                "available_certifications": list(all_certifications),
                "available_data_residencies": list(all_data_residencies),
                "note": "Match certifications and data_residency against user requirements to determine compliance.",
            }

        except Exception as e:
            return {"error": f"Failed to get compliance info: {str(e)}"}
