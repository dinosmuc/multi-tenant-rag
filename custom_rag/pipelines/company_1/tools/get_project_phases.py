"""Tool for getting project timeline and phases."""

from typing import Any

from custom_rag.core.base_tool import BaseTool
from custom_rag.pipelines.company_1.models import Product, ProjectPhase


class GetProjectPhasesTool(BaseTool):
    """Get project timeline and deliverables for Projekt-type products."""

    @property
    def name(self) -> str:
        return "get_project_phases"

    @property
    def description(self) -> str:
        return """Get detailed project timeline with phases and deliverables.
        Use for products with product_type='Projekt' to understand implementation timeline.
        Returns phases in order with duration and deliverables for each."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of product IDs to get project phases for (should be Projekt-type products)",
                }
            },
            "required": ["product_ids"],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Get project phases from project_phases table.

        Args:
            args: Tool arguments with product_ids
            context: Request context with db connection

        Returns:
            Dict with project timelines and phases
        """
        db = context.get("db")
        if not db:
            return {"error": "Database connection not available"}

        product_ids = args.get("product_ids", [])
        if not product_ids:
            return {"error": "No product IDs provided"}

        try:
            session = db.get_session()

            # Get product info
            products_query = (
                session.query(Product).filter(Product.id.in_(product_ids)).all()
            )
            product_info = {p.id: p for p in products_query}

            # Get project phases
            phases_query = (
                session.query(ProjectPhase)
                .filter(ProjectPhase.product_id.in_(product_ids))
                .order_by(ProjectPhase.product_id, ProjectPhase.phase_order)
                .all()
            )

            # Organize by product
            projects = []
            for product_id in product_ids:
                product = product_info.get(product_id)
                if not product:
                    projects.append(
                        {
                            "product_id": product_id,
                            "error": "Product not found",
                        }
                    )
                    continue

                product_phases = [p for p in phases_query if p.product_id == product_id]

                if not product_phases:
                    projects.append(
                        {
                            "product_id": product_id,
                            "product_name": product.name,
                            "product_type": product.product_type,
                            "warning": "No project phases defined",
                            "estimated_duration_weeks": f"{product.project_duration_min_weeks}-{product.project_duration_max_weeks}",
                        }
                    )
                    continue

                phases = []
                total_duration = 0
                for phase in product_phases:
                    phases.append(
                        {
                            "phase_order": phase.phase_order,
                            "phase_name": phase.phase_name,
                            "duration_min_weeks": phase.duration_min_weeks,
                            "deliverables": phase.deliverables or [],
                        }
                    )
                    total_duration += phase.duration_min_weeks or 0

                projects.append(
                    {
                        "product_id": product_id,
                        "product_name": product.name,
                        "product_type": product.product_type,
                        "total_duration_weeks": total_duration,
                        "duration_range_weeks": f"{product.project_duration_min_weeks}-{product.project_duration_max_weeks}",
                        "total_phases": len(phases),
                        "phases": phases,
                        "project_assumptions": product.project_assumptions or [],
                    }
                )

            session.close()

            return {
                "projects": projects,
                "total_products": len(projects),
            }

        except Exception as e:
            return {"error": f"Failed to get project phases: {str(e)}"}
