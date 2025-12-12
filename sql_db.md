# Database Schema Documentation

**Project:** Agentic RAG Product Catalog
**Database Name:** `blccoredemo`
**Architecture:** Star Schema (Hub-and-Spoke)
**Main Entity:** `products`



## 1. Entity Relationship Overview

* **One Product** relates to **Many** Billing Components (e.g., Setup Fee + Monthly License)
* **One Product** relates to **Many** Project Phases (e.g., Audit -> Migration -> Training)
* **One Product** relates to **Many** Dependencies (e.g., "SAP S/4HANA" requires "HANA Database")
* **One Product** relates to **Many** Market Segments (defining availability for SMB vs Enterprise)

## 2. Table Definitions

### Table 1: `products` (The Hub)
**Purpose:** The single source of truth for every product or service. Contains static, core information, technical parameters, and the full descriptive text for the RAG agent.

| Column | Type | Description |
| :--- | :--- | :--- |
| **`id`** | `VARCHAR(50)` | **PRIMARY KEY**. Unique product code (e.g., `SAP-001`). |
| `name` | `VARCHAR(255)` | Official product name in English. |
| `vendor` | `VARCHAR(100)` | Vendor name (e.g., `SAP`, `Microsoft`, `AWS`). |
| `product_type` | `ENUM` | `Projekt`, `SLA`, `Handelsware`, `Lizenz`. |
| `service_family` | `ENUM` | `SAP`, `Cloud`, `Workplace`, `Security`, `Network`, `Consulting`. |
| `lifecycle_status` | `ENUM` | `Active`, `Preview`, `Deprecated`, `EndOfSale`. |
| `is_standard_portfolio` | `TINYINT(1)` | `1` = Standard, `0` = Custom/Bespoke. |
| `full_description` | `TEXT` | Comprehensive 600+ word description of the service. |
| `key_benefits` | `JSON` | Array of strings listed as bullet points. |
| `use_cases` | `JSON` | Array of strings describing ideal customer scenarios. |
| `target_customer` | `TEXT` | Description of the ideal buyer persona. |
| `data_residency` | `ENUM` | `Switzerland`, `EU`, `Global`, `Customer_Choice`. |
| `certifications` | `JSON` | Array of relevant certs (e.g., `["ISO 27001", "SAP Certified"]`). |
| `sla_support_hours` | `ENUM` | `Business_Hours`, `8x5`, `12x5`, `24x5`, `24x7`. |
| `sla_response_critical` | `VARCHAR(50)` | Guaranteed response time (e.g., "15 Minutes"). |
| `sla_response_high` | `VARCHAR(50)` | Response time for High priority. |
| `sla_response_medium` | `VARCHAR(50)` | Response time for Medium priority. |
| `sla_response_low` | `VARCHAR(50)` | Response time for Low priority. |
| `sla_uptime_guarantee` | `VARCHAR(20)` | Uptime percentage (e.g., "99.9%"). |
| `sla_included_services` | `JSON` | Array of services included in the recurring fee. |
| `sla_excluded_services` | `JSON` | Array of services explicitly excluded. |
| `sla_contract_term_months_min`| `INT` | Minimum contract duration. |
| `sla_contract_term_months_standard`| `INT` | Standard contract duration. |
| `project_duration_min_weeks` | `INT` | Minimum estimated project duration. |
| `project_duration_max_weeks` | `INT` | Maximum estimated project duration. |
| `project_assumptions` | `JSON` | Technical prerequisites for the project. |
| `project_customer_resources` | `JSON` | Resources required from the customer side. |
| `fulfillment_type` | `ENUM` | `Automated`, `Manual`, `Consulting`, `Hybrid`. |
| `provisioning_time_min_days` | `INT` | Fastest possible delivery time. |
| `provisioning_time_max_days` | `INT` | Slowest expected delivery time. |
| `infrastructure_cloud_provider` | `ENUM` | `Azure`, `AWS`, `GCP`, `Any`, `On_Premise`, `Hybrid`. |
| `infrastructure_requirements` | `JSON` | Specific hardware/cloud requirements. |
| `owner_team` | `VARCHAR(100)` | Internal team responsible for delivery. |
| `owner_email` | `VARCHAR(255)` | Contact email for the product owner. |
| `internal_notes` | `TEXT` | Private notes for internal staff. |

### Table 2: `billing_components`
**Purpose:** Defines *how* a product is billed. Enables the RAG agent to calculate TCO (Total Cost of Ownership).

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `INT` | Primary Key (Auto-increment). |
| **`product_id`** | `VARCHAR(50)` | **Foreign Key** linking to `products.id`. |
| `component_id` | `VARCHAR(50)` | Unique SKU for this cost component. |
| `component_name` | `VARCHAR(255)` | Name of the cost item (e.g., "Installation Fee"). |
| `billing_model` | `ENUM` | `One_Time`, `Monthly`, `Yearly`, `Per_Unit`, `T_and_M`. |
| `unit_of_measure` | `ENUM` | `User`, `Device`, `GB`, `Hour`, `Project`, `Flat`, `Percentage`. |
| `tier_name` | `VARCHAR(100)` | Name of tier if applicable (e.g., "Gold Tier"). |
| `min_quantity` | `INT` | Minimum order quantity. |
| `max_quantity` | `INT` | Maximum order quantity (cap). |
| `price_chf` | `DECIMAL(12,2)` | Price in Swiss Francs. |
| `price_eur` | `DECIMAL(12,2)` | Price in Euros (optional). |
| `is_mandatory` | `TINYINT(1)` | `1` = Required cost, `0` = Optional add-on. |
| `applies_to_segments` | `JSON` | Array of segments this price applies to. |

### Table 3: `project_phases`
**Purpose:** For `Projekt` type products, this breaks down the delivery timeline so the agent can explain the "How".

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `INT` | Primary Key. |
| **`product_id`** | `VARCHAR(50)` | **Foreign Key** linking to `products.id`. |
| `phase_id` | `VARCHAR(50)` | Unique ID for the phase (e.g., `SAP-001-P1`). |
| `billing_component_id` | `VARCHAR(50)` | Optional link to a specific billing trigger. |
| `phase_name` | `VARCHAR(255)` | Name of the phase (e.g., "Phase 1: Discovery"). |
| `phase_order` | `INT` | Sequence number (1, 2, 3...). |
| `duration_min_weeks` | `INT` | Minimum estimated duration for this phase. |
| `duration_max_weeks` | `INT` | Maximum estimated duration for this phase. |
| `deliverables` | `JSON` | List of documents or milestones produced. |

### Table 4: `dependencies`
**Purpose:** Maps technical or commercial relationships between products. Essential for avoiding "hallucinated" solutions that are technically impossible.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `INT` | Primary Key. |
| **`product_id`** | `VARCHAR(50)` | **Foreign Key**. The product being requested. |
| **`depends_on_product_id`** | `VARCHAR(50)` | **Foreign Key**. The product that is *required* or *recommended*. |
| `dependency_type` | `ENUM` | `required`, `recommended`, `optional`, `incompatible`. |
| `reason` | `TEXT` | Explanation for the AI (e.g., "Requires S/4HANA core"). |

### Table 5: `market_segments`
**Purpose:** Defines availability or variations of a product for different customer sizes.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `INT` | Primary Key. |
| **`product_id`** | `VARCHAR(50)` | **Foreign Key** linking to `products.id`. |
| `segment` | `ENUM` | `MID-Market`, `Enterprise`, `SMB`. |
| `is_available` | `TINYINT(1)` | If the product is sold to this segment. |
| `default_description` | `TEXT` | Segment-specific marketing text (optional). |
| `included_users` | `INT` | Base users included for this segment (optional). |
| `included_hours` | `INT` | Base hours included for this segment (optional). |
| `sla_tier` | `ENUM` | `Standard`, `Silver`, `Gold`, `Platinum`. |

### Table 6: `platform_compatibility`
**Purpose:** Technical constraints regarding what hardware or software the product runs on.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `INT` | Primary Key. |
| **`product_id`** | `VARCHAR(50)` | **Foreign Key** linking to `products.id`. |
| `platform_name` | `VARCHAR(255)` | e.g., "Windows Server", "SAP BTP". |
| `platform_version` | `VARCHAR(100)` | e.g., "2019", "v2.0+". |
| `compatibility_notes` | `TEXT` | Detailed technical notes (e.g., "Global Admin required"). |