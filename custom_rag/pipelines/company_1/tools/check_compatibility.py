"""Tool for checking platform compatibility and technical requirements."""

from typing import Any

from custom_rag.core.base_tool import BaseTool
from custom_rag.pipelines.company_1.models import (
    Dependency,
    PlatformCompatibility,
    Product,
)


class CheckCompatibilityTool(BaseTool):
    """Check technical compatibility and platform requirements."""

    @property
    def name(self) -> str:
        return "check_compatibility"

    @property
    def description(self) -> str:
        return """Check technical compatibility for selected products.

        Returns:
        - incompatibilities: Products that CANNOT be used together (100% accurate from database)
        - platform_requirements: What platforms/versions each product requires

        The incompatibilities check is definitive - if products are marked incompatible in the database, they cannot be used together.

        YOU should compare platform_requirements against customer's environment to identify potential issues."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of product IDs to check compatibility for",
                },
            },
            "required": ["product_ids"],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Check compatibility from platform_compatibility and dependencies tables.

        Args:
            args: Tool arguments with product_ids
            context: Request context with db connection

        Returns:
            Dict with incompatibilities (definitive) and platform requirements (for model to analyze)
        """
        db = context.get("db")
        if not db:
            return {"error": "Database connection not available"}

        product_ids = args.get("product_ids", [])
        if not product_ids:
            return {"error": "No product IDs provided"}

        try:
            session = db.get_session()

            # Get product names
            products = session.query(Product).filter(Product.id.in_(product_ids)).all()
            product_names = {p.id: p.name for p in products}
            product_infra = {p.id: p.infrastructure_cloud_provider for p in products}

            # Check for incompatible dependencies (100% accurate - from database)
            incompatible_deps = (
                session.query(Dependency)
                .filter(
                    Dependency.product_id.in_(product_ids),
                    Dependency.depends_on_product_id.in_(product_ids),
                    Dependency.dependency_type == "incompatible",
                )
                .all()
            )

            # Get platform compatibility requirements
            platform_reqs = (
                session.query(PlatformCompatibility)
                .filter(PlatformCompatibility.product_id.in_(product_ids))
                .all()
            )

            # Build incompatibilities list (definitive)
            incompatibilities = []
            for dep in incompatible_deps:
                incompatibilities.append({
                    "product_id": dep.product_id,
                    "product_name": product_names.get(dep.product_id, "Unknown"),
                    "incompatible_with_id": dep.depends_on_product_id,
                    "incompatible_with_name": product_names.get(dep.depends_on_product_id, "Unknown"),
                    "reason": dep.reason,
                })

            # Build platform requirements (for model to analyze)
            platform_requirements = []
            for product_id in product_ids:
                product_platforms = [p for p in platform_reqs if p.product_id == product_id]

                platforms = []
                for plat in product_platforms:
                    platforms.append({
                        "platform_name": plat.platform_name,
                        "platform_version": plat.platform_version,
                        "compatibility_notes": plat.compatibility_notes,
                    })

                platform_requirements.append({
                    "product_id": product_id,
                    "product_name": product_names.get(product_id, "Unknown"),
                    "infrastructure_cloud_provider": product_infra.get(product_id),
                    "platforms": platforms if platforms else None,
                })

            session.close()

            # Compatibility is 100% determined by incompatibilities in database
            has_incompatibilities = len(incompatibilities) > 0

            return {
                "has_incompatibilities": has_incompatibilities,
                "incompatibilities": incompatibilities,
                "platform_requirements": platform_requirements,
                "note": "incompatibilities are definitive (from database). Compare platform_requirements against customer environment yourself.",
            }

        except Exception as e:
            return {"error": f"Failed to check compatibility: {str(e)}"}
