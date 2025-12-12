"""Tool for calculating pricing and TCO."""

from decimal import Decimal
from typing import Any

from custom_rag.core.base_tool import BaseTool
from custom_rag.pipelines.company_1.models import BillingComponent, Product


class GetPricingTool(BaseTool):
    """Calculate pricing and Total Cost of Ownership for products."""

    @property
    def name(self) -> str:
        return "get_pricing"

    @property
    def description(self) -> str:
        return """Calculate complete pricing for selected products including all billing components.
        Returns line items with one-time, monthly, and yearly costs, plus 3-year TCO.
        Use after finalizing product selection to build cost estimates."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of product IDs to price",
                },
                "quantities": {
                    "type": "object",
                    "description": "Optional quantities for per-unit billing (e.g., {'users': 200, 'devices': 50})",
                },
            },
            "required": ["product_ids"],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Calculate pricing from billing_components table.

        Args:
            args: Tool arguments with product_ids and optional quantities
            context: Request context with db connection

        Returns:
            Dict with detailed pricing breakdown and TCO
        """
        db = context.get("db")
        if not db:
            return {"error": "Database connection not available"}

        product_ids = args.get("product_ids", [])
        quantities = args.get("quantities", {})

        if not product_ids:
            return {"error": "No product IDs provided"}

        try:
            session = db.get_session()

            # Get product names
            products_query = (
                session.query(Product).filter(Product.id.in_(product_ids)).all()
            )
            product_names = {p.id: p.name for p in products_query}

            # Get billing components for all products
            components_query = (
                session.query(BillingComponent)
                .filter(BillingComponent.product_id.in_(product_ids))
                .all()
            )

            # Organize by product
            line_items = []
            one_time_total = Decimal("0")
            monthly_total = Decimal("0")
            yearly_total = Decimal("0")

            for product_id in product_ids:
                product_components = [
                    c for c in components_query if c.product_id == product_id
                ]

                if not product_components:
                    line_items.append(
                        {
                            "product_id": product_id,
                            "product_name": product_names.get(
                                product_id, "Unknown Product"
                            ),
                            "components": [],
                            "warning": "No billing components found",
                        }
                    )
                    continue

                components_list = []
                for component in product_components:
                    # Determine quantity
                    quantity = 1
                    if (
                        component.unit_of_measure
                        and component.unit_of_measure.lower()
                        in [
                            "user",
                            "users",
                        ]
                    ):
                        quantity = quantities.get(
                            "users", quantities.get("quantity", 1)
                        )
                    elif (
                        component.unit_of_measure
                        and component.unit_of_measure.lower()
                        in [
                            "device",
                            "devices",
                        ]
                    ):
                        quantity = quantities.get(
                            "devices", quantities.get("quantity", 1)
                        )

                    # Apply min_quantity
                    if component.min_quantity:
                        quantity = max(quantity, component.min_quantity)

                    # Apply max_quantity cap
                    if component.max_quantity:
                        quantity = min(quantity, component.max_quantity)

                    # Calculate total
                    unit_price = component.price_chf or Decimal("0")
                    total = unit_price * Decimal(str(quantity))

                    # Add to totals based on billing model
                    if component.billing_model == "One_Time":
                        one_time_total += total
                    elif component.billing_model == "Monthly":
                        monthly_total += total
                    elif component.billing_model == "Yearly":
                        yearly_total += total

                    component_info = {
                        "component_name": component.component_name,
                        "billing_model": component.billing_model,
                        "unit_of_measure": component.unit_of_measure,
                        "quantity": quantity,
                        "unit_price_chf": float(unit_price),
                        "total_chf": float(total),
                        "is_mandatory": component.is_mandatory,
                    }

                    # Include optional new fields if present
                    if component.tier_name:
                        component_info["tier_name"] = component.tier_name
                    if component.price_eur:
                        component_info["unit_price_eur"] = float(component.price_eur)
                        component_info["total_eur"] = float(
                            component.price_eur * Decimal(str(quantity))
                        )
                    if component.applies_to_segments:
                        component_info[
                            "applies_to_segments"
                        ] = component.applies_to_segments

                    components_list.append(component_info)

                line_items.append(
                    {
                        "product_id": product_id,
                        "product_name": product_names.get(
                            product_id, "Unknown Product"
                        ),
                        "components": components_list,
                    }
                )

            # Calculate summary
            yearly_from_monthly = monthly_total * 12
            total_yearly = yearly_total + yearly_from_monthly
            three_year_tco = one_time_total + (total_yearly * 3)

            session.close()

            return {
                "line_items": line_items,
                "summary": {
                    "one_time_total_chf": float(one_time_total),
                    "monthly_total_chf": float(monthly_total),
                    "yearly_total_chf": float(total_yearly),
                    "three_year_tco_chf": float(three_year_tco),
                },
                "quantities_applied": quantities if quantities else None,
            }

        except Exception as e:
            return {"error": f"Failed to calculate pricing: {str(e)}"}
