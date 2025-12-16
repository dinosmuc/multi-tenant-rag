"""Tool for retrieving pricing information."""

from typing import Any

from custom_rag.core.base_tool import BaseTool
from custom_rag.pipelines.company_1.models import BillingComponent, MarketSegment, Product


class GetPricingTool(BaseTool):
    """Retrieve all pricing information for products."""

    @property
    def name(self) -> str:
        return "get_pricing"

    @property
    def description(self) -> str:
        return """Retrieve all pricing and billing component information for products.

        Returns all billing components with:
        - component_name: Description that may include pricing logic (e.g., "Base fee covers up to 100 users")
        - billing_model: One_Time, Monthly, Yearly, Per_Unit, T_and_M
        - unit_of_measure: Flat, User, Device, GB, Hour, Project, Percentage
        - price_chf: Unit price in CHF
        - min_quantity: Minimum/block size (e.g., 50 means "per 50 users")
        - max_quantity: Maximum/cap or included quantity
        - is_mandatory: Whether component is required
        - tier_name: Tier if applicable (Gold, Silver, etc.)

        Also returns market segment info with included_users and included_hours if available.

        YOU must calculate the final price based on the component descriptions and user's quantities."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of product IDs to get pricing for",
                },
            },
            "required": ["product_ids"],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Retrieve all pricing information from billing_components and market_segments.

        Args:
            args: Tool arguments with product_ids
            context: Request context with db connection

        Returns:
            Dict with all billing components and segment info for the model to calculate
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
            product_info = {p.id: {"name": p.name, "product_type": p.product_type} for p in products}

            # Get ALL billing components with ALL fields
            components = (
                session.query(BillingComponent)
                .filter(BillingComponent.product_id.in_(product_ids))
                .order_by(BillingComponent.product_id, BillingComponent.is_mandatory.desc())
                .all()
            )

            # Get market segments (may have included_users/hours)
            segments = (
                session.query(MarketSegment)
                .filter(MarketSegment.product_id.in_(product_ids))
                .all()
            )

            # Organize by product
            pricing_data = []
            for product_id in product_ids:
                product_components = [c for c in components if c.product_id == product_id]
                product_segments = [s for s in segments if s.product_id == product_id]

                # Build component list with ALL fields
                components_list = []
                for comp in product_components:
                    comp_data = {
                        "component_id": comp.component_id,
                        "component_name": comp.component_name,
                        "billing_model": comp.billing_model,
                        "unit_of_measure": comp.unit_of_measure,
                        "price_chf": float(comp.price_chf) if comp.price_chf else None,
                        "price_eur": float(comp.price_eur) if comp.price_eur else None,
                        "min_quantity": comp.min_quantity,
                        "max_quantity": comp.max_quantity,
                        "is_mandatory": comp.is_mandatory,
                        "tier_name": comp.tier_name,
                        "applies_to_segments": comp.applies_to_segments,
                    }
                    components_list.append(comp_data)

                # Build segment list
                segments_list = []
                for seg in product_segments:
                    seg_data = {
                        "segment": seg.segment,
                        "is_available": seg.is_available,
                        "included_users": seg.included_users,
                        "included_hours": seg.included_hours,
                        "sla_tier": seg.sla_tier,
                    }
                    segments_list.append(seg_data)

                pricing_data.append({
                    "product_id": product_id,
                    "product_name": product_info.get(product_id, {}).get("name", "Unknown"),
                    "product_type": product_info.get(product_id, {}).get("product_type"),
                    "billing_components": components_list,
                    "market_segments": segments_list if segments_list else None,
                })

            session.close()

            return {
                "pricing": pricing_data,
                "note": "Review component_name for pricing logic. Use min_quantity as block size, max_quantity as cap or included amount. Calculate totals based on user's requirements.",
            }

        except Exception as e:
            return {"error": f"Failed to get pricing: {str(e)}"}
