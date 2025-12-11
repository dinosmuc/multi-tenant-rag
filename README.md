# Custom RAG Pipeline System

A scalable RAG (Retrieval-Augmented Generation) pipeline system for the BlueCallom platform, enabling individual companies to have completely isolated custom RAG implementations.

**This is a standalone Django project** that can later be integrated into the main BlueCallom platform.

## Project Structure

```
custom-rag/
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions CI/CD
├── config/                       # Django project configuration
│   ├── __init__.py
│   ├── settings.py              # Django settings
│   ├── urls.py                  # Root URL configuration
│   ├── wsgi.py                  # WSGI config
│   └── asgi.py                  # ASGI config
│
├── custom_rag/                  # Main Django app
│   ├── core/                    # Shared base classes
│   │   ├── base_pipeline.py     # Abstract base for pipelines
│   │   ├── base_tool.py         # Abstract base for tools
│   │   ├── agent_executor.py    # Agentic loop logic
│   │   ├── llm_provider.py      # Abstract LLM provider
│   │   ├── openai_provider.py   # OpenAI Responses API implementation
│   │   └── provider_factory.py  # Dynamic provider creation
│   ├── connectors/              # Database connectors
│   │   ├── database.py          # SQLAlchemy wrapper
│   │   └── weaviate_connector.py # Weaviate wrapper
│   ├── pipelines/               # Company-specific implementations
│   │   ├── _template/           # Template for new pipelines
│   │   └── company_1/           # Example pipeline
│   ├── urls.py                  # App URL routing
│   ├── views.py                 # REST API endpoint
│   ├── registry.py              # Pipeline loader
│   ├── utils.py                 # Response helpers
│   └── pipelines.json           # Pipeline config mapping
│
├── tests/                       # Pytest test suite
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures
│   ├── test_connectors.py       # Connector tests
│   ├── test_registry.py         # Registry tests
│   └── test_views.py            # Views tests
│
├── manage.py                    # Django management script
├── pytest.ini                   # Pytest configuration
├── pyproject.toml               # Project config
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Dev dependencies (incl. pytest)
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## Key Features

- **Complete Isolation**: Each company's pipeline runs in isolation with no shared state
- **Multi-Provider Support**: Supports OpenAI (with extensibility for Anthropic, etc.)
- **Dynamic Provider Selection**: Frontend controls which LLM provider to use
- **Reasoning Models Support**: Full support for o1/o3 with reasoning_effort parameter
- **Token Tracking**: Complete usage tracking for cost monitoring
- **Config-Driven**: All company-specific values from configuration
- **Fresh Connections**: New database connections per request
- **Automatic Cleanup**: Resources released after each request using context managers
- **Standardized Errors**: Clean error responses with error codes
- **Test Coverage**: Comprehensive pytest test suite
- **CI/CD**: Automated testing and linting via GitHub Actions

## Prerequisites

- **Python 3.11+**
- **pip** (Python package manager)
- **Git**
- **MySQL or PostgreSQL** (for company databases)
- **Weaviate** (vector database - via Docker or cloud)
- **OpenAI API key**

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd custom-rag
```

### 2. Create and activate virtual environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### 3. Install dependencies

```bash
# Install all dependencies including dev tools (Recommended)
pip install -r requirements-dev.txt

# Or production only
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
# Copy template
copy .env.example .env     # Windows
cp .env.example .env       # macOS/Linux

# Generate a Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Edit .env and add:
# - Generated SECRET_KEY
# - OPENAI_API_KEY (REQUIRED)
# - WEAVIATE_URL (REQUIRED)
# - WEAVIATE_API_KEY (REQUIRED)
# - Company database URLs
```

**Required Environment Variables:**
```env
# Django
SECRET_KEY=your-generated-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# OpenAI (REQUIRED)
OPENAI_API_KEY=sk-your-api-key-here

# Weaviate (REQUIRED)
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-weaviate-api-key

# Company Databases
COMPANY1_DB_URL=mysql://user:password@host:port/database
```

### 5. Run Django migrations

```bash
python manage.py migrate
```

### 6. Run development server

```bash
python manage.py runserver
```

Visit: http://localhost:8000/admin/

## Setting Up Weaviate (Vector Database)

### Option 1: Docker (Recommended for local development)

```bash
docker run -d \
  -p 8080:8080 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  --name weaviate \
  semitechnologies/weaviate:latest
```

### Option 2: Weaviate Cloud

1. Sign up at https://console.weaviate.cloud/
2. Create a cluster
3. Copy the cluster URL and API key to your `.env` file

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_connectors.py

# Run with coverage
pytest --cov=custom_rag tests/
```

## Code Quality Tools

```bash
# Format code with Black
black .

# Lint with Ruff
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Run all quality checks (what CI runs)
black --check . && ruff check . && pytest tests/
```

## API Endpoint

### Request Format

```http
POST /custom_rag/execute/
Content-Type: application/json

{
  "function_id": "company_1",
  "llm_provider": "openai",
  "llm": "gpt-4o",
  "reasoning_effort": "medium",  // Optional, for o1/o3 models
  "prompt_objects": {
    "query": "What products do we have?"
  },
  "scope_variables": {},
  "previous_prompt_outputs": {}
}
```

### Success Response

```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "output": "We have the following products...",
    "metadata": {
      "iterations": 5,
      "tools_used": ["semantic_search", "get_product_details"]
    }
  },
  "usage": {
    "input_tokens": 123,
    "output_tokens": 456,
    "total_tokens": 579
  }
}
```

### Error Response

```json
{
  "success": false,
  "statusCode": 400,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Missing 'function_id' in request"
  },
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0
  }
}
```

### Error Codes

- `INVALID_REQUEST` - Missing or invalid request parameters
- `PIPELINE_NOT_FOUND` - Pipeline function_id not found
- `PROVIDER_NOT_SUPPORTED` - LLM provider not supported
- `INVALID_JSON` - Request body is not valid JSON
- `INTERNAL_ERROR` - Unexpected server error

## Adding a New Pipeline

1. Copy the `_template` folder to a new company folder:
   ```bash
   cp -r custom_rag/pipelines/_template custom_rag/pipelines/company_name
   ```

2. Implement company-specific components:
   - `models.py` - SQLAlchemy models
   - `config.py` - Configuration constants
   - `tools/` - Custom tools
   - `prompts/system_prompt.py` - System prompt
   - `pipeline.py` - Pipeline implementation

3. Add configuration to `pipelines.json`:
   ```json
   {
     "company_name_rag": {
       "pipeline": "custom_rag.pipelines.company_name.pipeline.RAGPipeline",
       "config": {
         "weaviate_collection": "CompanyNameCollection",
         "db_env_var": "COMPANY_NAME_DB_URL",
         "max_iterations": 100
       }
     }
   }
   ```

4. Add database URL to `.env`:
   ```env
   COMPANY_NAME_DB_URL=mysql://user:password@host:port/database
   ```

See `project.md` for detailed documentation.

## CI/CD

GitHub Actions automatically runs on every push and PR:

✅ **Ruff** - Code linting
✅ **Black** - Code formatting check
✅ **Pytest** - Full test suite

PRs must pass all checks before merging to main.

## Development Workflow

1. Create feature branch
2. Make changes
3. Run tests locally: `pytest`
4. Format code: `black .`
5. Check linting: `ruff check .`
6. Commit and push
7. GitHub Actions runs automatically
8. Create PR when checks pass

## Architecture Overview

```
Request → Views → Registry → Pipeline Factory
                      ↓
                  Pipeline (with context manager)
                      ↓
              Provider Factory → OpenAI/Anthropic
                      ↓
              Agent Executor (agentic loop)
                      ↓
              Tools (semantic search, DB queries, etc.)
                      ↓
                  Response with usage tracking
```

## License

Proprietary - BlueCallom

## Support

For issues or questions, please contact the development team or refer to `project.md` for detailed documentation.
