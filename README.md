# Custom RAG Pipeline System

A flexible, provider-agnostic Retrieval-Augmented Generation (RAG) pipeline framework built with Django. It enables building agentic workflows that combine LLMs with tools for database queries, vector search, and external APIs — with full per-request isolation and automatic resource management.

## Features

- **Dynamic LLM provider selection** — per-request model and provider switching (OpenAI supported, extensible to Anthropic, etc.)
- **Agentic tool-calling loop** — autonomous multi-step reasoning with configurable iteration limits (up to 100)
- **Dual data layer** — SQL (SQLAlchemy) for structured queries + Weaviate for semantic vector search
- **Progressive answer building** — incremental result construction to prevent information loss in long chains
- **Token tracking** — accumulated usage metrics across all iterations for cost monitoring
- **Context manager pipelines** — per-request resource isolation with guaranteed cleanup
- **Pipeline registry** — config-driven pipeline discovery and instantiation via `pipelines.json`
- **Reasoning effort control** — support for OpenAI o1/o3 reasoning effort levels

## Architecture

```
Request → Django View → Registry → Pipeline (Context Manager)
                                       │
                                  Provider Factory → LLM Provider
                                       │
                                  Agent Executor ⇄ Tools (SQL, Vector DB, APIs)
                                       │
                                  Progressive Answer Builder → Response
```

### Core Components

| Component | Purpose |
|---|---|
| `core/llm_provider.py` | Abstract LLM provider interface |
| `core/openai_provider.py` | OpenAI Responses API implementation |
| `core/provider_factory.py` | Factory for dynamic provider creation |
| `core/agent_executor.py` | Agentic loop with tool dispatch |
| `core/base_pipeline.py` | Abstract pipeline with context manager pattern |
| `core/base_tool.py` | Abstract tool base class |
| `connectors/database.py` | SQLAlchemy connector with connection pooling |
| `connectors/weaviate_connector.py` | Weaviate vector DB connector |

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Weaviate instance (cloud or local)
- MySQL or PostgreSQL database

### Setup

```bash
# Clone and enter the project
git clone <repository-url>
cd custom-rag

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials (see .env.example for required variables)

# Run migrations and start the server
python manage.py migrate
python manage.py runserver
```

The API is available at `http://localhost:8000/custom_rag/execute/`.

## Usage

### API Request

```bash
curl -X POST http://localhost:8000/custom_rag/execute/ \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "company_1",
    "llm_provider": "openai",
    "llm": "gpt-4o",
    "reasoning_effort": "medium",
    "prompt_objects": {
      "query": "Find SAP products for mid-market customers with Swiss data residency"
    }
  }'
```

### Response

```json
{
  "success": true,
  "data": {
    "output": { ... },
    "iterations": 12,
    "tools_used": ["semantic_search", "get_product_details", "get_pricing", "create_final_answer"]
  },
  "usage": {
    "input_tokens": 4200,
    "output_tokens": 1800,
    "total_tokens": 6000
  }
}
```

### Request Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `function_id` | string | Yes | Pipeline identifier (e.g., `"company_1"`) |
| `llm_provider` | string | Yes | Provider name (`"openai"`) |
| `llm` | string | Yes | Model name (`"gpt-4o"`, `"o3-mini"`, etc.) |
| `reasoning_effort` | string | No | For reasoning models: `"low"`, `"medium"`, `"high"` |
| `prompt_objects` | object | Yes | Input data (e.g., `{"query": "..."}`) |

## Project Structure

```
custom-rag/
├── config/                        # Django project settings
├── custom_rag/
│   ├── views.py                   # REST API endpoint
│   ├── registry.py                # Pipeline discovery and registration
│   ├── utils.py                   # Response helpers and error codes
│   ├── core/                      # Framework abstractions
│   │   ├── base_pipeline.py       # Abstract pipeline (context manager)
│   │   ├── base_tool.py           # Abstract tool interface
│   │   ├── agent_executor.py      # Agentic loop executor
│   │   ├── llm_provider.py        # Abstract LLM provider
│   │   ├── openai_provider.py     # OpenAI implementation
│   │   └── provider_factory.py    # Provider factory
│   ├── connectors/                # Database and vector DB connectors
│   └── pipelines/                 # Pipeline implementations
│       └── company_1/             # Example: product catalog pipeline
│           ├── pipeline.py        # Pipeline orchestration
│           ├── models.py          # SQLAlchemy ORM models
│           ├── prompts/           # System and planning prompts
│           └── tools/             # 9 domain-specific tools
├── tests/                         # Test suite (38 tests, pytest)
├── pyproject.toml                 # Project config, Black/Ruff settings
├── requirements.txt               # Production dependencies
└── requirements-dev.txt           # Development dependencies
```

## Extending

### Adding a New Pipeline

1. Create a directory under `custom_rag/pipelines/your_pipeline/`
2. Implement a pipeline class extending `BasePipeline`
3. Create tools extending `BaseTool`
4. Write system/planning prompts
5. Register in `custom_rag/pipelines/pipelines.json`

See `custom_rag/pipelines/company_1/` for a complete reference implementation.

### Adding a New LLM Provider

1. Create a provider class extending `LLMProvider`
2. Implement `execute_with_tools()`
3. Register in `ProviderFactory`

## Testing

```bash
pytest                                        # Run all tests (38 tests)
pytest tests/test_company_1_pipeline.py -v    # Run specific test file
pytest --cov=custom_rag --cov-report=html     # Coverage report
```

All tests use mocks — no real API calls or database connections required.

## Code Quality

```bash
black .              # Format
ruff check . --fix   # Lint
pytest               # Test
```

## Tech Stack

- **Python 3.11+** / **Django** — web framework and API layer
- **SQLAlchemy** — ORM with connection pooling
- **Weaviate** — vector database for semantic search
- **OpenAI Responses API** — LLM provider with tool calling
- **pytest** — testing framework

## License

This project is proprietary software. All rights reserved.
