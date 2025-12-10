# Custom RAG Pipeline System

A scalable RAG (Retrieval-Augmented Generation) pipeline system for the BlueCallom platform, enabling individual companies to have completely isolated custom RAG implementations.

**This is a standalone Django project** that can later be integrated into the main BlueCallom platform.

## Project Structure

```
custom-rag/
├── config/                      # Django project configuration
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
│   │   └── agent_executor.py    # Agentic loop logic
│   ├── connectors/              # Database connectors
│   │   ├── database.py          # SQLAlchemy wrapper
│   │   └── weaviate_connector.py # Weaviate wrapper
│   ├── pipelines/               # Company-specific implementations
│   │   └── _template/           # Template for new pipelines
│   │       ├── pipeline.py
│   │       ├── config.py
│   │       ├── models.py
│   │       ├── tools/
│   │       └── prompts/
│   ├── urls.py                  # App URL routing
│   ├── views.py                 # REST API endpoint
│   ├── registry.py              # Pipeline loader
│   └── pipelines.json           # Pipeline config mapping
│
├── manage.py                    # Django management script
├── pyproject.toml               # Project config & dependencies
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Dev dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## Key Features

- **Complete Isolation**: Each company's pipeline runs in isolation with no shared state
- **Config-Driven**: All company-specific values come from configuration
- **Fresh Connections**: New database connections per request
- **Automatic Cleanup**: Resources released after each request using context managers
- **Extensible**: Easy to add new pipelines without modifying core framework

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
# Recommended: install all dependencies (incl. dev tools)
pip install -r requirements-dev.txt

# Optional: editable install (only if you adjust package discovery)
# pip install -e ".[dev]"
# To make this work you would need to configure package discovery
# (because both `config` and `custom_rag` are top-level).
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
# - OPENAI_API_KEY
# - WEAVIATE_URL
# - Company database URLs
```

### 5. Run Django migrations

```bash
python manage.py migrate
```

### 6. Create superuser (optional)

```bash
python manage.py createsuperuser
```

### 7. Run development server

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

## Running the Project

```bash
# Make sure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Run development server
python manage.py runserver

# Run with custom port
python manage.py runserver 8001
```

## Code Quality Tools

```bash
# Format code with Black
black .

# Lint with Ruff
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Run tests
pytest
```

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
