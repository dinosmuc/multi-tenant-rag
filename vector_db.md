# Vector Database Schema

**Project:** Agentic RAG Product Catalog
**Platform:** Weaviate Cloud
**Collection Name:** `Company1Products`
**Embedding Model:** `text-embedding-3-large` (OpenAI)

## 1. Collection Structure

The collection `Company1Products` is configured to store unstructured product data for semantic search.

### Property Definitions

| Property Name | Data Type | Filterable | Description |
| :--- | :--- | :--- | :--- |
| **`product_id`** | `text` | **Yes** | Primary identifier. Links to the SQL database. |
| `name` | `text` | Yes | Official product name. |
| `description` | `text` | No | Combined short and full descriptions. |
| `benefits` | `text` | No | Key product benefits. |
| `use_cases` | `text` | No | Ideal customer scenarios. |
| `product_type` | `text` | **Yes** | Category (`Projekt`, `SLA`, `Handelsware`, `Lizenz`). |
| `service_family` | `text` | **Yes** | Grouping (`SAP`, `Cloud`, `Security`, etc.). |
| `lifecycle_status` | `text` | Yes | Status (`Active`, `Deprecated`, etc.). |
| `data_residency` | `text` | Yes | Data location (`Switzerland`, `EU`, `Global`). |
| `is_standard` | `boolean` | Yes | Standard portfolio flag (`True`/`False`). |

## 2. Configuration Details

* **Vector Dimensions:** 3072
* **Vectorizer:** `text-embedding-3-large`
* **Searchable Properties:** `name`, `description`, `benefits`, `use_cases`
* **Filterable Properties:** `service_family`, `product_type`, `data_residency`, `is_standard`, `lifecycle_status`