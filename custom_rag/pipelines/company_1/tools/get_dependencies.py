"""Tool for finding product dependencies."""

from typing import Any

from custom_rag.core.base_tool import BaseTool
from custom_rag.pipelines.company_1.models import Dependency, Product


class GetDependenciesTool(BaseTool):
    """Find required and recommended dependencies for products."""

    @property
    def name(self) -> str:
        return "get_dependencies"

    @property
    def description(self) -> str:
        return """Find all product dependencies including required, recommended, optional, and incompatible relationships.
        Critical for building complete solutions - always call this after selecting products.
        Returns 'required' (must have), 'recommended' (should have), 'optional' (nice to have), and 'incompatible' (cannot use together)."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of product IDs to check dependencies for",
                }
            },
            "required": ["product_ids"],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Find dependencies from dependencies table.

        Args:
            args: Tool arguments with product_ids
            context: Request context with db connection

        Returns:
            Dict with required and recommended dependencies
        """
        db = context.get("db")
        if not db:
            return {"error": "Database connection not available"}

        product_ids = args.get("product_ids", [])
        if not product_ids:
            return {"error": "No product IDs provided"}

        try:
            session = db.get_session()

            # Get dependencies
            dependencies_query = (
                session.query(Dependency)
                .filter(Dependency.product_id.in_(product_ids))
                .all()
            )

            # Get product names for both sides
            all_product_ids = list(product_ids)
            all_product_ids.extend(
                [d.depends_on_product_id for d in dependencies_query]
            )
            products_query = (
                session.query(Product).filter(Product.id.in_(all_product_ids)).all()
            )
            product_names = {p.id: p.name for p in products_query}

            # Organize by product
            dependencies_map = []
            for product_id in product_ids:
                product_deps = [
                    d for d in dependencies_query if d.product_id == product_id
                ]

                required = []
                recommended = []
                optional = []
                incompatible = []

                for dep in product_deps:
                    dep_info = {
                        "product_id": dep.depends_on_product_id,
                        "product_name": product_names.get(
                            dep.depends_on_product_id, "Unknown Product"
                        ),
                        "dependency_type": dep.dependency_type,
                        "reason": dep.reason,
                    }

                    if dep.dependency_type == "required":
                        required.append(dep_info)
                    elif dep.dependency_type == "recommended":
                        recommended.append(dep_info)
                    elif dep.dependency_type == "optional":
                        optional.append(dep_info)
                    elif dep.dependency_type == "incompatible":
                        incompatible.append(dep_info)

                dependencies_map.append(
                    {
                        "product_id": product_id,
                        "product_name": product_names.get(
                            product_id, "Unknown Product"
                        ),
                        "required": required,
                        "recommended": recommended,
                        "optional": optional,
                        "incompatible": incompatible,
                        "total_dependencies": len(required)
                        + len(recommended)
                        + len(optional),
                    }
                )

            # Get unique list of all required dependencies
            all_required = []
            for deps in dependencies_map:
                all_required.extend([r["product_id"] for r in deps["required"]])
            all_required = list(set(all_required))

            session.close()

            return {
                "dependencies": dependencies_map,
                "all_required_product_ids": all_required,
                "total_required_dependencies": len(all_required),
            }

        except Exception as e:
            return {"error": f"Failed to get dependencies: {str(e)}"}
