"""SQLAlchemy ORM models for Company_1 database schema."""

from sqlalchemy import DECIMAL, JSON, Boolean, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Product(Base):
    """Products table - Hub of the star schema."""

    __tablename__ = "products"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    vendor = Column(String(100))
    product_type = Column(String(50))
    service_family = Column(String(50))
    lifecycle_status = Column(String(50))
    is_standard_portfolio = Column(Boolean)
    full_description = Column(Text)
    key_benefits = Column(JSON)
    use_cases = Column(JSON)
    target_customer = Column(Text)
    data_residency = Column(String(50))
    certifications = Column(JSON)
    sla_support_hours = Column(String(50))
    sla_response_critical = Column(String(50))
    sla_response_high = Column(String(50))
    sla_response_medium = Column(String(50))
    sla_response_low = Column(String(50))
    sla_uptime_guarantee = Column(String(20))
    sla_included_services = Column(JSON)
    sla_excluded_services = Column(JSON)
    sla_contract_term_months_min = Column(Integer)
    sla_contract_term_months_standard = Column(Integer)
    project_duration_min_weeks = Column(Integer)
    project_duration_max_weeks = Column(Integer)
    project_assumptions = Column(JSON)
    project_customer_resources = Column(JSON)
    fulfillment_type = Column(String(50))
    provisioning_time_min_days = Column(Integer)
    provisioning_time_max_days = Column(Integer)
    infrastructure_cloud_provider = Column(String(50))
    infrastructure_requirements = Column(JSON)
    owner_team = Column(String(100))
    owner_email = Column(String(255))
    internal_notes = Column(Text)


class BillingComponent(Base):
    """Billing components table - Pricing information."""

    __tablename__ = "billing_components"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), nullable=False)
    component_id = Column(String(50))
    component_name = Column(String(255))
    billing_model = Column(String(50))
    unit_of_measure = Column(String(50))
    tier_name = Column(String(100))
    min_quantity = Column(Integer)
    max_quantity = Column(Integer)
    price_chf = Column(DECIMAL(12, 2))
    price_eur = Column(DECIMAL(12, 2))
    is_mandatory = Column(Boolean)
    applies_to_segments = Column(JSON)


class ProjectPhase(Base):
    """Project phases table - Timeline and deliverables."""

    __tablename__ = "project_phases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), nullable=False)
    phase_id = Column(String(50))
    billing_component_id = Column(String(50))
    phase_name = Column(String(255))
    phase_order = Column(Integer)
    duration_min_weeks = Column(Integer)
    duration_max_weeks = Column(Integer)
    deliverables = Column(JSON)


class Dependency(Base):
    """Dependencies table - Product relationships."""

    __tablename__ = "dependencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), nullable=False)
    depends_on_product_id = Column(String(50), nullable=False)
    dependency_type = Column(String(50))
    reason = Column(Text)


class MarketSegment(Base):
    """Market segments table - Product availability by segment."""

    __tablename__ = "market_segments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), nullable=False)
    segment = Column(String(50))
    is_available = Column(Boolean)
    default_description = Column(Text)
    included_users = Column(Integer)
    included_hours = Column(Integer)
    sla_tier = Column(String(50))


class PlatformCompatibility(Base):
    """Platform compatibility table - Technical requirements."""

    __tablename__ = "platform_compatibility"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), nullable=False)
    platform_name = Column(String(255))
    platform_version = Column(String(100))
    compatibility_notes = Column(Text)
