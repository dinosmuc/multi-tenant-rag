"""Tool for checking platform compatibility and technical requirements."""

from typing import Any

from custom_rag.core.base_tool import BaseTool
from custom_rag.pipelines.company_1.models import (
    Dependency,
    PlatformCompatibility,
    Product,
)


class CheckCompatibilityTool(BaseTool):
    """Verify technical compatibility and platform requirements."""

    @property
    def name(self) -> str:
        return "check_compatibility"

    @property
    def description(self) -> str:
        return """Check technical compatibility and platform requirements for selected products.
        Verifies platform requirements and checks for incompatible product combinations.
        Use before finalizing solution to ensure everything works together."""

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
                "customer_context": {
                    "type": "object",
                    "description": "Optional customer current state (e.g., {'current_platform': 'Windows Server 2016', 'users': 200})",
                },
            },
            "required": ["product_ids"],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Check compatibility from platform_compatibility and dependencies tables.

        Args:
            args: Tool arguments with product_ids and optional customer_context
            context: Request context with db connection

        Returns:
            Dict with compatibility status, platform requirements, and warnings
        """
        db = context.get("db")
        if not db:
            return {"error": "Database connection not available"}

        product_ids = args.get("product_ids", [])
        customer_context = args.get("customer_context", {})

        if not product_ids:
            return {"error": "No product IDs provided"}

        try:
            session = db.get_session()

            # Get product names
            products_query = (
                session.query(Product).filter(Product.id.in_(product_ids)).all()
            )
            product_names = {p.id: p.name for p in products_query}

            # Get platform compatibility requirements
            platform_reqs = (
                session.query(PlatformCompatibility)
                .filter(PlatformCompatibility.product_id.in_(product_ids))
                .all()
            )

            # Check for incompatible dependencies
            incompatible_deps = (
                session.query(Dependency)
                .filter(
                    Dependency.product_id.in_(product_ids),
                    Dependency.depends_on_product_id.in_(product_ids),
                    Dependency.dependency_type == "incompatible",
                )
                .all()
            )

            # Organize platform requirements
            platform_requirements = []
            for product_id in product_ids:
                product_platforms = [
                    p for p in platform_reqs if p.product_id == product_id
                ]

                if product_platforms:
                    platforms = []
                    for plat in product_platforms:
                        platform_info = {
                            "name": plat.platform_name,
                            "version": plat.platform_version,
                        }
                        # Include compatibility notes if present
                        if plat.compatibility_notes:
                            platform_info["notes"] = plat.compatibility_notes
                        platforms.append(platform_info)

                    platform_requirements.append(
                        {
                            "product_id": product_id,
                            "product_name": product_names.get(
                                product_id, "Unknown Product"
                            ),
                            "platforms": platforms,
                        }
                    )

            # Check for incompatibilities
            issues = []
            for incomp in incompatible_deps:
                issues.append(
                    {
                        "severity": "critical",
                        "message": f"Incompatibility: {product_names.get(incomp.product_id)} cannot be used with {product_names.get(incomp.depends_on_product_id)}",
                        "reason": incomp.reason,
                        "affected_products": [
                            incomp.product_id,
                            incomp.depends_on_product_id,
                        ],
                    }
                )

            # Generate warnings based on customer context
            warnings = []
            if customer_context.get("current_platform"):
                current_platform = customer_context["current_platform"].lower()
                for req in platform_requirements:
                    for platform in req["platforms"]:
                        if platform["name"].lower() not in current_platform:
                            warnings.append(
                                {
                                    "severity": "medium",
                                    "message": f"{req['product_name']} requires {platform['name']} {platform['version']}",
                                    "affected_products": [req["product_id"]],
                                    "recommendation": f"Customer may need to upgrade from {customer_context['current_platform']}",
                                }
                            )

            # Determine overall compatibility
            compatible = len(issues) == 0

            session.close()

            return {
                "compatible": compatible,
                "issues": issues,
                "warnings": warnings,
                "platform_requirements": platform_requirements,
                "customer_context_provided": bool(customer_context),
            }

        except Exception as e:
            return {"error": f"Failed to check compatibility: {str(e)}"}
