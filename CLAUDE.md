# CLAUDE.md - Custom RAG Pipeline System

This file provides context for Claude Code instances working on this codebase.

## Project Overview

**Custom RAG** is a flexible, provider-agnostic Retrieval-Augmented Generation (RAG) pipeline system. It enables building agentic workflows that combine LLMs with tools for database queries, vector search, and external APIs.

### Key Features
- Dynamic LLM provider selection (currently OpenAI, extensible to Anthropic, etc.)
- Reasoning effort support for reasoning models (o1, o3-mini)
- Agentic loop with tool calling (up to 100 iterations)
- Progressive answer building to prevent information loss
- Token tracking across iterations
- Context manager pattern for resource cleanup
- Comprehensive logging for debugging
- Full test suite with 38 passing tests (pytest)

## Folder Structure

```
custom-rag/
├── config/                           # Django project configuration
│   ├── settings.py                   # Django settings + logging config
│   ├── urls.py                       # Root URL routing
│   ├── wsgi.py                       # WSGI config
│   └── asgi.py                       # ASGI config
│
├── custom_rag/                       # Main application package
│   ├── views.py                      # REST API endpoint (execute_pipeline)
│   ├── urls.py                       # App-level URL routing
│   ├── registry.py                   # Pipeline registration system
│   ├── utils.py                      # Response helpers, ErrorCodes
│   │
│   ├── connectors/                   # External service connectors
│   │   ├── database.py               # SQLAlchemy database connector
│   │   └── weaviate_connector.py    # Weaviate vector DB connector
│   │
│   ├── core/                         # Core abstractions and implementations
│   │   ├── base_tool.py              # Abstract tool base class
│   │   ├── base_pipeline.py          # Abstract pipeline base class
│   │   ├── llm_provider.py           # Abstract LLM provider interface
│   │   ├── openai_provider.py        # OpenAI Responses API implementation
│   │   ├── provider_factory.py       # Factory for creating providers
│   │   └── agent_executor.py         # Agentic loop executor
│   │
│   └── pipelines/                    # Pipeline implementations
│       ├── pipelines.json            # Pipeline metadata/configuration
│       │
│       └── company_1/                # Company_1 product catalog pipeline (IMPLEMENTED)
│           ├── pipeline.py           # Main pipeline implementation
│           ├── models.py             # SQLAlchemy ORM models (6 tables)
│           ├── config.py             # Pipeline-specific configuration
│           │
│           ├── prompts/              # Prompt templates
│           │   └── system_prompt.py  # 430-line system prompt with DB schemas
│           │
│           └── tools/                # 9 pipeline-specific tools
│               ├── semantic_search.py           # Vector search for discovery
│               ├── get_product_details.py       # SQL query for full product info
│               ├── get_pricing.py               # TCO calculation
│               ├── get_dependencies.py          # Find required/recommended products
│               ├── get_project_phases.py        # Project timeline
│               ├── check_compatibility.py       # Platform verification
│               ├── filter_by_compliance.py      # Regulatory filtering
│               ├── build_answer.py              # Progressive answer construction
│               └── submit_final_answer.py       # Loop breaking tool
│
├── tests/                            # Test suite (38 tests)
│   ├── conftest.py                   # Pytest fixtures and configuration
│   ├── test_connectors.py            # Database & Weaviate connector tests (6 tests)
│   ├── test_registry.py              # Pipeline registry tests (7 tests)
│   ├── test_views.py                 # REST API endpoint tests (4 tests)
│   └── test_company_1_pipeline.py    # Company_1 pipeline tests (21 tests)
│
├── logs/                             # Log output directory
│   └── custom_rag.log                # File logs with timestamps
│
├── .env                              # Environment variables (not in git)
├── .env.example                      # Environment variable template
├── .gitignore                        # Git ignore patterns
├── CLAUDE.md                         # This file - guide for Claude instances
├── README.md                         # How to run the project
├── project.md                        # Original project specification
├── sql_db.md                         # SQL database schema documentation
├── vector_db.md                      # Weaviate schema documentation
├── manage.py                         # Django management script
├── pytest.ini                        # Pytest configuration
├── pyproject.toml                    # Project metadata, Black/Ruff config
├── requirements.txt                  # Production dependencies
└── requirements-dev.txt              # Development dependencies
```

## Common Commands

```bash
# Activate virtual environment
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

# Run Django development server
python manage.py runserver

# Run all tests
pytest

# Run tests with coverage
pytest --cov=custom_rag --cov-report=html

# Run specific test file
pytest tests/test_company_1_pipeline.py -v

# Skip integration tests
pytest -v -m "not integration"

# Format code
black .

# Lint code
ruff check .

# Fix linting issues
ruff check . --fix
```

## Architecture Overview

### High-Level Flow

```
Frontend Request → Django View → Registry → Pipeline (Context Manager)
                                              ↓
                                         Provider Factory
                                              ↓
                                         LLM Provider (OpenAI)
                                              ↓
                                         Agent Executor
                                              ↓
                                         Tools (DB, Weaviate, APIs)
                                              ↓
                                         Progressive Answer Building
                                              ↓
                                         Response with Token Usage
```

### Core Components

#### 1. Provider Abstraction Layer
- `LLMProvider` (abstract base class) - Defines interface for all LLM providers
- `OpenAIProvider` - Implements OpenAI Responses API with reasoning_effort
- `ProviderFactory` - Creates provider instances dynamically

**Location:** `custom_rag/core/`

**Key Design Decision:** Frontend specifies both `llm_provider` and `llm` (model) in every request, enabling per-request model selection.

#### 2. Pipeline System
- `BasePipeline` - Abstract base class with context manager pattern
- Pipelines are instantiated per request and automatically cleaned up
- Each pipeline registers itself via `pipelines.json`

**Location:** `custom_rag/pipelines/`

**Context Manager Pattern:**
```python
with PipelineClass(config) as pipeline:
    result = pipeline.execute(context)
# Resources automatically cleaned up here
```

#### 3. Agent Executor
- Implements agentic loop (max 100 iterations by default)
- Delegates to LLM provider for tool calling logic
- Tracks iterations and accumulates usage stats

**Location:** `custom_rag/core/agent_executor.py`

#### 4. Connectors
- `DatabaseConnector` - SQLAlchemy wrapper with connection pooling (`pool_pre_ping=True`)
- `WeaviateConnector` - Vector database client for semantic search

**Location:** `custom_rag/connectors/`

#### 5. Tools
- `BaseTool` - Abstract base class defining tool interface
- Each tool implements `execute(args, context)` method
- Tools receive context dict with db/weaviate connections

**Location:** `custom_rag/core/base_tool.py` and `custom_rag/pipelines/*/tools/`

#### 6. Context Passing
- Context flows: Pipeline → AgentExecutor → LLMProvider → Tools
- Contains: db, weaviate, answer_builder, prompt_objects, llm_provider
- Fixed architecture ensures all tools receive necessary resources

#### 7. Logging System
- Console logging with simple format
- File logging with timestamps to `logs/custom_rag.log`
- Logs every iteration, tool call, tool result, completion
- Configured in `config/settings.py`

### Request/Response Flow

**Request Format:**
```json
{
  "function_id": "company_1",
  "llm_provider": "openai",
  "llm": "gpt-4o",
  "reasoning_effort": "medium",
  "prompt_objects": {
    "query": "Show me SAP products for mid-market"
  }
}
```

**Response Format (Success):**
```json
{
  "success": true,
  "data": {
    "output": {
      "task_type": "gap_analysis",
      "matched_requirements": [...],
      "pricing_summary": {...}
    },
    "iterations": 15,
    "tools_used": ["semantic_search", "get_pricing", "build_answer", "submit_final_answer"]
  },
  "usage": {
    "input_tokens": 5000,
    "output_tokens": 2000,
    "total_tokens": 7000
  }
}
```

**Response Format (Error):**
```json
{
  "success": false,
  "error": {
    "code": "PIPELINE_NOT_FOUND",
    "message": "Pipeline 'invalid_id' not found in registry"
  }
}
```

**Error Codes:** See `ErrorCodes` class in `custom_rag/utils.py`

## Database Schemas

### SQL Database (Star Schema)
- **Hub:** `products` table (35+ fields, comprehensive product data)
- **Spokes:** `billing_components`, `project_phases`, `dependencies`, `market_segments`, `platform_compatibility`
- **Purpose:** Structured data for pricing, dependencies, technical specs

**Schema:** See `sql_db.md`

### Vector Database (Weaviate)
- **Collection:** `Company1Products`
- **Embedding Model:** `text-embedding-3-large` (3072 dimensions)
- **Searchable Properties:** name, description, benefits, use_cases
- **Filterable Properties:** service_family, product_type, data_residency, lifecycle_status

**Schema:** See `vector_db.md`

## Company_1 Pipeline Implementation

### Overview
Fully implemented product catalog RAG pipeline for analyzing customer requirements against Company_1's catalog of 100 SAP/Cloud products.

**Supports three main task types:**
- **Gap Analysis** - Match requirements against available products
- **Solution Design** - Build complete solutions with dependencies
- **Pricing** - Calculate costs and TCO

### Agent Workflow

1. **Analyze Request** - Identify task type and extract requirements
2. **Create Plan** - Agent has complete freedom, no step limits
3. **Set Goal** - Define clear success criteria
4. **Execute with Tools** - Use all 9 tools as needed
5. **Build Answer Progressively** - Call `build_answer` after EVERY finding
6. **Continue Until Goal Achieved** - Review completeness before submitting
7. **Submit Final Answer** - MUST call `submit_final_answer` to break loop

### Nine Tools

**Discovery Tools:**
1. `semantic_search` - Vector search in Weaviate with filters
2. `filter_by_compliance` - Filter by certifications and data residency

**Analysis Tools:**
3. `get_product_details` - SQL query for complete product information
4. `get_dependencies` - Find required/recommended/incompatible products
5. `check_compatibility` - Verify platform requirements

**Costing Tools:**
6. `get_pricing` - Calculate TCO with billing components
7. `get_project_phases` - Get project timeline and deliverables

**Orchestration Tools:**
8. `build_answer` - Progressive answer construction (prevents information loss)
9. `submit_final_answer` - Break loop and return complete answer (ONLY way to finish)

### Progressive Answer Building

**Problem:** Large responses can exceed token limits or lose information in long agentic loops.

**Solution:** The `build_answer` tool stores findings progressively throughout execution.

```python
# Agent calls build_answer after EVERY significant finding
build_answer(
    section="matched_requirements",
    action="add",
    data={"requirement": "SAP S/4HANA", "status": "matched"}
)

# At the end, submit_final_answer returns the complete answer_builder
submit_final_answer(summary="Analysis complete", confidence="high")
```

**Sections in answer_builder:**
- `task_type` - Gap Analysis / Solution Design / Pricing
- `matched_requirements` - Products matching requirements
- `unmatched_requirements` - Requirements with no solution
- `recommended_products` - Product recommendations
- `dependencies` - Required and recommended dependencies
- `pricing_summary` - Cost breakdown and TCO
- `compliance_status` - Regulatory compliance info
- `confidence_scores` - Confidence per requirement

### System Prompt

**File:** `custom_rag/pipelines/company_1/prompts/system_prompt.py`

**430 lines including:**
- Complete SQL schema for all 6 tables
- Complete Weaviate schema
- Agent role and task types
- 7-step workflow instructions
- Tool usage guidelines with examples
- Output structure specifications
- Important rules (progressive building, loop breaking)

## Testing Strategy

### Test Coverage (38 tests)

**Framework Tests (17 tests):**
- `test_connectors.py` - Database and Weaviate connectors (6 tests)
- `test_registry.py` - Pipeline registration (7 tests)
- `test_views.py` - REST API endpoints (4 tests)

**Company_1 Pipeline Tests (21 tests):**
- `test_company_1_pipeline.py` - Pipeline, tools, context passing (21 tests)

### Testing Approach
- All tests use mocks for external dependencies (OpenAI API, databases)
- No real API calls or database connections in tests
- Test isolation via `conftest.py` fixtures
- Environment variables auto-set in test environment

### Running Tests
```bash
# Run all tests
pytest -v

# Run only company_1 tests
pytest tests/test_company_1_pipeline.py -v

# Run with coverage
pytest --cov=custom_rag --cov-report=html

# Skip integration tests
pytest -v -m "not integration"
```

**Expected Result:** 38/38 tests passing

## Logging System

### Configuration
**File:** `config/settings.py` lines 113-177

**Handlers:**
- Console: Simple format (levelname + message)
- File: Verbose format (levelname + timestamp + module + message)
- Output: `logs/custom_rag.log`

**Loggers:**
- `custom_rag.core.openai_provider` - Agent executor logs
- `custom_rag.pipelines.company_1.pipeline` - Pipeline logs

### Log Output Example

```
================================================================================
🎯 COMPANY_1 PIPELINE STARTED
================================================================================
📝 Query: Show me SAP products for mid-market customers
🗄️  Database: Connected
🔍 Weaviate: Connected
🤖 LLM: <OpenAIProvider object>
================================================================================

🚀 Starting agentic loop
🔄 Max iterations: 100

================================================================================
🔄 ITERATION 1/100
================================================================================

🔧 Tool Call: semantic_search
📥 Arguments: {
  "query": "SAP products for mid-market",
  "top_k": 10
}
📤 Tool Result: {"products": [...], "total_found": 5}

================================================================================
🔄 ITERATION 2/100
================================================================================

🔧 Tool Call: build_answer
📥 Arguments: {"section": "matched_requirements", "action": "add", ...}
📤 Tool Result: {"success": true, "sections_completed": 1}

...

================================================================================
✅ Loop completed: Agent returned final output
📊 Total iterations: 15
🔧 Tools used: semantic_search, get_pricing, build_answer, submit_final_answer
📈 Token usage: 5000 in / 2000 out
================================================================================

✅ COMPANY_1 PIPELINE COMPLETED
📊 Iterations used: 15
🔧 Total tool calls: 8
```

## Key Design Decisions

### 1. Dynamic Provider Selection
- **Why:** Enables frontend to choose provider and model per request
- **How:** `ProviderFactory.create_provider(provider_name, model, reasoning_effort)`
- **Impact:** Easy to add new providers (Anthropic, etc.) without changing pipelines

### 2. Context Manager Pattern for Pipelines
- **Why:** Ensures database connections and resources are always cleaned up
- **How:** `__enter__` creates connections, `__exit__` closes them
- **Impact:** No resource leaks, even if pipeline execution fails

### 3. Context Passing Architecture
- **Why:** Tools need access to db, weaviate, answer_builder
- **How:** Context threaded through AgentExecutor → LLMProvider → Tools
- **Impact:** All tools receive necessary resources

### 4. Progressive Answer Building
- **Why:** Large responses exceed token limits, information can be lost in long loops
- **How:** `build_answer` tool stores findings incrementally
- **Impact:** Complete answers even with 50+ tool calls

### 5. Loop Breaking Tool
- **Why:** Agent needs explicit way to signal completion
- **How:** `submit_final_answer` returns answer_builder and breaks loop
- **Impact:** Clear completion signal, no ambiguity

### 6. High Iteration Limit (100)
- **Why:** Complex RAG tasks may require many tool calls
- **How:** Default `max_iterations=100` in AgentExecutor
- **Impact:** Prevents premature termination of complex reasoning chains

### 7. Reasoning Effort Parameter
- **Why:** OpenAI o1/o3 models support effort levels (low, medium, high)
- **How:** Optional parameter passed through to Responses API
- **Impact:** Frontend controls compute tradeoff for reasoning models

### 8. Token Tracking Across Iterations
- **Why:** Agentic loops make multiple LLM calls, need total usage
- **How:** Provider accumulates tokens in `total_input_tokens` and `total_output_tokens`
- **Impact:** Accurate cost tracking and usage monitoring

### 9. Comprehensive Logging
- **Why:** Debug agentic loops, understand agent behavior
- **How:** Log every iteration, tool call, result, completion
- **Impact:** Easy debugging when triggered via Postman or API

## Environment Variables

Required environment variables (see `.env.example`):

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# OpenAI
OPENAI_API_KEY=sk-...

# Database (per company)
COMPANY_1_DB_URL=mysql://user:pass@host:port/blccoredemo

# Weaviate
WEAVIATE_URL=https://your-instance.weaviate.network
WEAVIATE_API_KEY=your-api-key
```

## Adding a New Pipeline

1. Create directory: `custom_rag/pipelines/your_pipeline/`
2. Implement pipeline class extending `BasePipeline`
3. Create tools extending `BaseTool`
4. Write system prompt
5. Register in `pipelines.json`
6. Write tests
7. Update documentation

**Example pipeline.py:**
```python
from custom_rag.core.base_pipeline import BasePipeline

class YourPipeline(BasePipeline):
    def get_tools(self) -> list[BaseTool]:
        return [YourTool1(), YourTool2()]

    def get_system_prompt(self) -> str:
        return "Your system prompt..."

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        # Initialize answer_builder
        context["answer_builder"] = {}
        context["db"] = self.db
        context["weaviate"] = self.weaviate

        # Create agent executor
        agent_executor = AgentExecutor(
            tools=self.tools,
            system_prompt=self.get_system_prompt(),
            llm_provider=context.get("llm_provider"),
            max_iterations=self.config.get("max_iterations", 100),
        )

        # Execute
        result = agent_executor.execute(context)

        return {
            "output": context.get("answer_builder", result.get("output")),
            "iterations": result.get("iterations"),
            "tools_used": result.get("tools_used"),
        }
```

## Adding a New LLM Provider

1. Create provider class in `custom_rag/core/`
2. Extend `LLMProvider` abstract base class
3. Implement `execute_with_tools()` method
4. Update `ProviderFactory` in `provider_factory.py`
5. Write tests

**Example:**
```python
from custom_rag.core.llm_provider import LLMProvider

class AnthropicProvider(LLMProvider):
    def execute_with_tools(
        self,
        instructions: str,
        user_message: str,
        tools: list[BaseTool],
        max_iterations: int,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Implement Anthropic API logic
        pass
```

## Current Status

- **Version:** Development (pre-1.0)
- **Test Coverage:** 38/38 tests passing
- **Supported Providers:** OpenAI (Anthropic planned)
- **Implemented Pipelines:** company_1 (fully implemented with 9 tools)
- **Logging:** Comprehensive logging for debugging
- **Database Status:** Schema ready, awaiting 100 product population

## Troubleshooting

### Common Issues

**Test Failures:**
- Ensure all environment variables are set (see conftest.py)
- Check exception handler ordering in views.py
- Verify mocks use `MagicMock` for context managers

**Provider Errors:**
- Check OPENAI_API_KEY is valid
- Verify model name is correct (gpt-4o, o1-preview, etc.)
- Ensure reasoning_effort only used with o1/o3 models

**Database Connection Issues:**
- Verify connection string format
- Check `pool_pre_ping=True` is enabled
- Ensure database is accessible from your network

**Weaviate Issues:**
- Verify WEAVIATE_URL and WEAVIATE_API_KEY
- Check collection name matches schema
- Ensure embedding model is correct

**Context Passing Issues:**
- Verify context is threaded through AgentExecutor → LLMProvider → Tools
- Check tools receive context in execute() method
- Ensure answer_builder is initialized in pipeline.execute()

**Loop Not Breaking:**
- Verify agent calls `submit_final_answer` tool
- Check system prompt instructs agent to call submit_final_answer
- Ensure submit_final_answer returns with status="completed"

## Contact

For questions or issues, refer to:
- `README.md` - How to run the project
- `project.md` - Original project specification
- `sql_db.md` - SQL database schema
- `vector_db.md` - Vector database schema
