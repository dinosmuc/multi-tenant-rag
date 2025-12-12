"""Tool for filtering products by compliance and regulatory requirements."""

from typing import Any

from custom_rag.core.base_tool import BaseTool
from custom_rag.pipelines.company_1.models import Product


class FilterByComplianceTool(BaseTool):
    """Filter products by regulatory and compliance requirements."""

    @property
    def name(self) -> str:
        return "filter_by_compliance"

    @property
    def description(self) -> str:
        return """Filter products by compliance requirements like certifications and data residency.
        Use FIRST if customer mentions ISO 27001, FINMA, Swiss data residency, or other regulatory needs.
        Returns only products that meet all specified requirements."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "requirements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of compliance requirements (e.g., ['ISO 27001', 'Swiss data residency', 'FINMA'])",
                },
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: narrow search to specific products (leave empty to search all products)",
                },
            },
            "required": ["requirements"],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Filter products by compliance requirements.

        Args:
            args: Tool arguments with requirements list and optional product_ids
            context: Request context with db connection

        Returns:
            Dict with compliant and non-compliant products
        """
        db = context.get("db")
        if not db:
            return {"error": "Database connection not available"}

        requirements = args.get("requirements", [])
        product_ids = args.get("product_ids")

        if not requirements:
            return {"error": "No requirements provided"}

        try:
            session = db.get_session()

            # Build query
            query = session.query(Product)
            if product_ids:
                query = query.filter(Product.id.in_(product_ids))

            all_products = query.all()

            compliant_products = []
            non_compliant_products = []

            for product in all_products:
                matched_requirements = []
                missing_requirements = []

                # Check each requirement
                for req in requirements:
                    req_lower = req.lower().strip()
                    matched = False

                    # Check data residency
                    if any(
                        keyword in req_lower
                        for keyword in ["swiss", "switzerland", "data residency"]
                    ):
                        if product.data_residency and (
                            "switzerland" in product.data_residency.lower()
                            or "swiss" in product.data_residency.lower()
                        ):
                            matched = True
                            matched_requirements.append(
                                f"Data residency: {product.data_residency}"
                            )

                    # Check certifications
                    if product.certifications:
                        cert_list = (
                            product.certifications
                            if isinstance(product.certifications, list)
                            else []
                        )
                        for cert in cert_list:
                            if req_lower in cert.lower():
                                matched = True
                                matched_requirements.append(cert)
                                break

                    # Check for FINMA (specific Swiss financial regulation)
                    if "finma" in req_lower:
                        if product.certifications and any(
                            "finma" in str(cert).lower()
                            for cert in product.certifications
                        ):
                            matched = True
                            matched_requirements.append("FINMA compliant")
                        elif (
                            product.data_residency
                            and "switzerland" in product.data_residency.lower()
                        ):
                            # If Swiss data residency, might be FINMA compliant
                            matched = True
                            matched_requirements.append(
                                "Swiss data residency (FINMA relevant)"
                            )

                    if not matched:
                        missing_requirements.append(req)

                # Classify product
                if not missing_requirements:
                    compliant_products.append(
                        {
                            "product_id": product.id,
                            "product_name": product.name,
                            "matched_requirements": list(set(matched_requirements)),
                            "certifications": product.certifications or [],
                            "data_residency": product.data_residency,
                            "compliance_score": 1.0,
                        }
                    )
                else:
                    compliance_score = len(matched_requirements) / len(requirements)
                    non_compliant_products.append(
                        {
                            "product_id": product.id,
                            "product_name": product.name,
                            "matched_requirements": list(set(matched_requirements)),
                            "missing_requirements": missing_requirements,
                            "certifications": product.certifications or [],
                            "data_residency": product.data_residency,
                            "compliance_score": round(compliance_score, 2),
                            "reason": f"Missing: {', '.join(missing_requirements)}",
                        }
                    )

            session.close()

            return {
                "compliant_products": compliant_products,
                "non_compliant_products": non_compliant_products,
                "total_compliant": len(compliant_products),
                "total_non_compliant": len(non_compliant_products),
                "requirements_checked": requirements,
            }

        except Exception as e:
            return {"error": f"Failed to filter by compliance: {str(e)}"}
