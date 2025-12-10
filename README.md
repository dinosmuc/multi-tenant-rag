# Custom RAG Pipeline System

A scalable RAG (Retrieval-Augmented Generation) pipeline system for the BlueCallom platform, enabling individual companies to have completely isolated custom RAG implementations.

## Project Structure

```
custom_rag/
├── core/                    # Shared base classes and utilities
│   ├── base_pipeline.py     # Abstract base class for all pipelines
│   ├── base_tool.py         # Abstract base class for all tools
│   └── agent_executor.py    # Agentic loop logic
├── connectors/              # Database and vector store connectors
│   ├── database.py          # SQLAlchemy wrapper
│   └── weaviate_connector.py # Weaviate client wrapper
├── pipelines/               # Company-specific implementations
│   └── _template/           # Template for new pipelines
│       ├── pipeline.py
│       ├── config.py
│       ├── models.py
│       ├── tools/
│       └── prompts/
├── urls.py                  # URL routing
├── views.py                 # REST API endpoint
├── registry.py              # Pipeline configuration loader
└── pipelines.json           # Pipeline configuration mapping
```

## Key Features

- **Complete Isolation**: Each company's pipeline runs in isolation with no shared state
- **Config-Driven**: All company-specific values come from configuration
- **Fresh Connections**: New database connections per request
- **Automatic Cleanup**: Resources released after each request using context managers
- **Extensible**: Easy to add new pipelines without modifying core framework

## Prerequisites

See installation section below for detailed requirements.

## Installation

1. Clone the repository
2. Create a virtual environment
3. Install dependencies
4. Configure environment variables
5. Run migrations (if needed)

## Configuration

Copy `.env.example` to `.env` and fill in your configuration values.

## Adding a New Pipeline

1. Copy the `_template` folder to a new company folder
2. Implement company-specific models, tools, and prompts
3. Add configuration to `pipelines.json`
4. Add database URL to environment variables

See `project.md` for detailed documentation.

## API Endpoint

```
POST /custom_rag/execute/
{
  "function_id": "company_rag_function",
  "prompt_objects": {...},
  "scope_variables": {...},
  "previous_prompt_outputs": {...},
  "llm": "gpt-4"
}
```

## License

Proprietary - BlueCallom
