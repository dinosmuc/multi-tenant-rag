"""Tool for finding product dependencies with recursive resolution."""

from typing import Any

from custom_rag.core.base_tool import BaseTool
from custom_rag.pipelines.company_1.models import Dependency, Product


class GetDependenciesTool(BaseTool):
    """Find required and recommended dependencies for products, including nested dependencies."""

    @property
    def name(self) -> str:
        return "get_dependencies"

    @property
    def description(self) -> str:
        return """Find all product dependencies including required, recommended, optional, and incompatible relationships.

        IMPORTANT: This tool returns NESTED dependencies - dependencies of dependencies are included automatically.
        You do NOT need to call this tool recursively. One call returns the full dependency tree.

        Returns for each dependency type:
        - 'required': Must have these products
        - 'recommended': Should have these products
        - 'optional': Nice to have
        - 'incompatible': Cannot use together

        Each dependency includes its own nested dependencies up to 5 levels deep."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of product IDs to check dependencies for",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth for nested dependencies (default: 5)",
                    "default": 5,
                },
            },
            "required": ["product_ids"],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Find dependencies recursively from dependencies table.

        Args:
            args: Tool arguments with product_ids and optional max_depth
            context: Request context with db connection

        Returns:
            Dict with nested dependencies for each product
        """
        db = context.get("db")
        if not db:
            return {"error": "Database connection not available"}

        product_ids = args.get("product_ids", [])
        if not product_ids:
            return {"error": "No product IDs provided"}

        max_depth = args.get("max_depth", 5)

        try:
            session = db.get_session()

            # Cache for product names (loaded on demand)
            product_names_cache = {}

            # Track all visited products to report flat list
            all_required_products = set()
            all_recommended_products = set()

            def get_product_name(product_id: str) -> str:
                """Get product name from cache or database."""
                if product_id not in product_names_cache:
                    product = session.query(Product).filter(Product.id == product_id).first()
                    product_names_cache[product_id] = product.name if product else "Unknown Product"
                return product_names_cache[product_id]

            def get_dependencies_recursive(
                product_id: str,
                depth: int,
                visited: set[str],
            ) -> dict[str, Any]:
                """
                Recursively get dependencies for a product.

                Args:
                    product_id: Product to get dependencies for
                    depth: Current depth level
                    visited: Set of already visited product IDs (prevents circular deps)

                Returns:
                    Dict with nested dependency information
                """
                # Prevent infinite loops and respect max depth
                if depth > max_depth or product_id in visited:
                    return None

                visited.add(product_id)

                # Query direct dependencies
                deps = (
                    session.query(Dependency)
                    .filter(Dependency.product_id == product_id)
                    .all()
                )

                required = []
                recommended = []
                optional = []
                incompatible = []

                for dep in deps:
                    dep_product_id = dep.depends_on_product_id
                    dep_product_name = get_product_name(dep_product_id)

                    # Track for flat list
                    if dep.dependency_type == "required":
                        all_required_products.add(dep_product_id)
                    elif dep.dependency_type == "recommended":
                        all_recommended_products.add(dep_product_id)

                    # Get nested dependencies (recursive call)
                    nested_deps = get_dependencies_recursive(
                        dep_product_id,
                        depth + 1,
                        visited.copy(),  # Copy to allow different paths
                    )

                    dep_info = {
                        "product_id": dep_product_id,
                        "product_name": dep_product_name,
                        "reason": dep.reason,
                    }

                    # Only add nested dependencies if they exist
                    if nested_deps:
                        dep_info["dependencies"] = nested_deps

                    if dep.dependency_type == "required":
                        required.append(dep_info)
                    elif dep.dependency_type == "recommended":
                        recommended.append(dep_info)
                    elif dep.dependency_type == "optional":
                        optional.append(dep_info)
                    elif dep.dependency_type == "incompatible":
                        incompatible.append(dep_info)

                # Return None if no dependencies at all
                if not (required or recommended or optional or incompatible):
                    return None

                result = {}
                if required:
                    result["required"] = required
                if recommended:
                    result["recommended"] = recommended
                if optional:
                    result["optional"] = optional
                if incompatible:
                    result["incompatible"] = incompatible

                return result

            # Process each requested product
            dependencies_map = []
            for product_id in product_ids:
                product_name = get_product_name(product_id)

                # Get recursive dependencies starting from depth 1
                deps = get_dependencies_recursive(product_id, 1, set())

                product_result = {
                    "product_id": product_id,
                    "product_name": product_name,
                }

                if deps:
                    product_result.update(deps)
                else:
                    product_result["required"] = []
                    product_result["recommended"] = []

                dependencies_map.append(product_result)

            session.close()

            return {
                "dependencies": dependencies_map,
                "all_required_product_ids": list(all_required_products),
                "all_recommended_product_ids": list(all_recommended_products),
                "total_unique_dependencies": len(all_required_products | all_recommended_products),
                "max_depth_used": max_depth,
            }

        except Exception as e:
            return {"error": f"Failed to get dependencies: {str(e)}"}
