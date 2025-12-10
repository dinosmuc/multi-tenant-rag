# Custom RAG Pipeline Architecture — Complete Reference

---

## 1. Overview

### 1.1 Purpose

This system enables individual companies on the BlueCallom platform to have their own custom RAG (Retrieval-Augmented Generation) pipelines. Each company's pipeline is completely isolated from others.

### 1.2 Key Principles

| Principle | Implementation |
|-----------|----------------|
| Isolation | Each request gets fresh pipeline instance |
| No shared state | No global variables, no shared cache |
| Fresh connections | New database connections per request |
| Config-driven | All company-specific values from config, never hardcoded |
| Cleanup | All resources released after each request |

### 1.3 How It Integrates with BlueCallom

User creates prompt in BlueCallom → Enables "Custom Model" toggle → Selects company RAG function → Prompt execution calls Python RAG pipeline → Pipeline returns JSON → Stored as prompt output → Available for next prompts

---

## 2. Tech Stack

### 2.1 Core Technologies

| Technology | Purpose |
|------------|---------|
| Python 3.11+ | Runtime |
| Django | Web framework |
| SQLAlchemy | Database ORM |
| Weaviate Client | Vector database |
| OpenAI | LLM provider |

### 2.2 Development Tools

| Tool | Purpose |
|------|---------|
| venv | Virtual environment |
| pip | Package management |
| Ruff | Linting |
| Black | Code formatting |

---

## 3. Flow Overview

**Step 1: User Creates Prompt**

User in their company creates a prompt with Custom Model toggle turned on and selects their company's RAG function.

**Step 2: Prompt Execution Triggers API Call**

```
POST /custom_rag/execute/

{
  "function_id": "<rag_function_name>",
  "prompt_objects": { ... },
  "scope_variables": { ... },
  "previous_prompt_outputs": { ... },
  "llm": "<model_name>"
}
```

**Step 3: Response Flow**

Python RAG pipeline returns JSON → Stored as prompt output → Next prompts can use it

---

## 4. File Structure

```
blcAPIPython/gptblue/
│
├── custom_rag/
│   │
│   ├── __init__.py
│   ├── urls.py                              # URL routing
│   ├── views.py                             # REST endpoint (entry point)
│   ├── registry.py                          # Loads pipelines.json, builds context
│   ├── pipelines.json                       # Maps function_id → pipeline config
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base_pipeline.py                 # Abstract base class for all pipelines
│   │   ├── base_tool.py                     # Abstract base class for all tools
│   │   └── agent_executor.py                # Agentic loop logic
│   │
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── weaviate_connector.py            # Weaviate client wrapper
│   │   └── database.py                      # SQLAlchemy database wrapper
│   │
│   └── pipelines/
│       ├── __init__.py
│       │
│       ├── _template/                       # Template for new pipelines
│       │   ├── __init__.py
│       │   ├── pipeline.py
│       │   ├── config.py
│       │   ├── models.py
│       │   ├── tools/
│       │   │   ├── __init__.py
│       │   │   └── example_tool.py
│       │   └── prompts/
│       │       ├── __init__.py
│       │       └── system_prompt.py
│       │
│       ├── {company_a}/
│       │   ├── __init__.py
│       │   ├── pipeline.py
│       │   ├── config.py
│       │   ├── models.py
│       │   ├── tools/
│       │   │   ├── __init__.py
│       │   │   ├── semantic_search.py
│       │   │   ├── get_product_details.py
│       │   │   └── get_pricing.py
│       │   └── prompts/
│       │       ├── __init__.py
│       │       └── system_prompt.py
│       │
│       └── {company_n}/
│           └── ...
│
├── requirements.txt                         # Dependencies
├── requirements-dev.txt                     # Dev dependencies
├── setup.cfg                                # Ruff, Black configuration
├── .gitignore
├── .env.example
└── README.md
```

---

## 5. Configuration Files

### 5.1 requirements.txt

Production dependencies: Django, SQLAlchemy, Weaviate client, OpenAI, Pydantic, python-dotenv.

### 5.2 requirements-dev.txt

Development dependencies: Ruff, Black.

### 5.3 setup.cfg

Configuration for Ruff (linting) and Black (formatting).

### 5.4 .gitignore

Ignores Python cache, virtual environments, IDE files, secrets, and OS files.

### 5.5 .env.example

Template for environment variables: Django settings, Weaviate URL, OpenAI API key, company database URLs.

---

## 6. Component Details

### 6.1 urls.py

**Purpose:** Register the REST endpoint with Django.

**Registers:** `POST /custom_rag/execute/` → `views.execute_pipeline`

---

### 6.2 views.py

**Purpose:** Single entry point for all RAG requests.

**Responsibilities:**
- Receive POST request
- Extract function_id and request data
- Call registry to get pipeline class and config
- Instantiate pipeline with context manager
- Execute pipeline
- Return formatted response
- Handle errors with standard try/except

**Request Format:**
```
{
  "function_id": "<function_id>",
  "prompt_objects": { ... },
  "scope_variables": { ... },
  "previous_prompt_outputs": { ... },
  "llm": "<model_name>"
}
```

**Response Format (Success):**
```
{
  "success": true,
  "output": { ... },
  "metadata": {
    "iterations": <number>,
    "tools_used": [ ... ]
  }
}
```

**Response Format (Error):**
```
{
  "success": false,
  "error": "<error_message>"
}
```

---

### 6.3 registry.py

**Purpose:** Load pipeline configuration and build request context.

**Responsibilities:**
- Load pipelines.json at module import
- Look up function_id
- Dynamically import pipeline class
- Build context dict from request data
- Return pipeline class, config, and context

**Methods:**

| Method | Purpose |
|--------|---------|
| `get_pipeline(function_id, request_data)` | Returns (pipeline_class, config, context) |
| `reload_config()` | Reloads pipelines.json without server restart |

---

### 6.4 pipelines.json

**Purpose:** Map function_id to pipeline class and configuration.

**Structure:**
```
{
  "<function_id>": {
    "pipeline": "<full.path.to.PipelineClass>",
    "config": {
      "weaviate_collection": "<collection_name>",
      "db_env_var": "<ENV_VAR_NAME>",
      "max_iterations": <number>
    }
  }
}
```

**Example:**
```
{
  "company_a_product_rag": {
    "pipeline": "custom_rag.pipelines.company_a.pipeline.RAGPipeline",
    "config": {
      "weaviate_collection": "CompanyAProducts",
      "db_env_var": "COMPANY_A_DB_URL",
      "max_iterations": 10
    }
  },
  "company_b_product_rag": {
    "pipeline": "custom_rag.pipelines.company_b.pipeline.RAGPipeline",
    "config": {
      "weaviate_collection": "CompanyBProducts",
      "db_env_var": "COMPANY_B_DB_URL",
      "max_iterations": 8
    }
  }
}
```

**Note:** `db_env_var` is the name of the environment variable that holds the database connection string. Pipeline reads it using `os.getenv()`.

---

### 6.5 core/base_pipeline.py

**Purpose:** Abstract base class that all pipelines inherit from.

**Methods:**

| Method | Purpose |
|--------|---------|
| `__init__(config)` | Store config |
| `__enter__()` | Initialize connections, load tools |
| `__exit__(...)` | Cleanup all resources |
| `get_tools()` | Return list of tool instances |
| `get_system_prompt()` | Return system prompt string |
| `execute(context)` | Run the pipeline, return result |

**Context Manager Pattern:**

`__enter__()`:
- Read database URL from environment using `os.getenv(config["db_env_var"])`
- Create SQLAlchemy engine + session
- Create Weaviate connection
- Load tools
- Return self

`__exit__()`:
- Close SQLAlchemy session
- Dispose SQLAlchemy engine
- Close Weaviate connection
- Set all references to None

---

### 6.6 core/base_tool.py

**Purpose:** Abstract base class that all tools inherit from.

**Properties:**

| Property | Type | Purpose |
|----------|------|---------|
| `name` | string | Tool identifier |
| `description` | string | What the tool does (shown to LLM) |
| `parameters` | dict | JSON schema of expected arguments |

**Methods:**

| Method | Purpose |
|--------|---------|
| `execute(args, context)` | Run the tool, return result |

---

### 6.7 core/agent_executor.py

**Purpose:** Run the agentic loop where LLM decides which tools to call.

**Input:**
- context
- tools (list of tool instances)
- system_prompt
- llm (model name)
- max_iterations

**Flow:**
```
1. Build initial messages (system + user)
2. Loop:
   a. Send messages + tools to LLM
   b. If tool call → Execute → Add to messages → Continue
   c. If final answer → Exit
   d. If max_iterations → Exit
3. Return output, iterations, tools_used
```

---

### 6.8 connectors/database.py

**Purpose:** SQLAlchemy database wrapper.

**Features:**
- Creates SQLAlchemy engine from connection string
- Session management

**Methods:**

| Method | Purpose |
|--------|---------|
| `__init__(connection_string)` | Create engine |
| `get_session()` | Get new session |
| `close()` | Close all connections |

---

### 6.9 connectors/weaviate_connector.py

**Purpose:** Wrapper for Weaviate client.

**Methods:**

| Method | Purpose |
|--------|---------|
| `__init__(collection)` | Connect to collection |
| `semantic_search(query, filters, top_k)` | Search by meaning |
| `get_by_ids(ids)` | Get objects by ID |
| `close()` | Close connection |

---

### 6.10 pipelines/{company}/pipeline.py

**Purpose:** Company-specific pipeline implementation.

**Inherits from:** BasePipeline

**Responsibilities:**
- Override `get_tools()` to return company's tools
- Override `get_system_prompt()` to return company's prompt
- Configure company-specific database connections

---

### 6.11 pipelines/{company}/config.py

**Purpose:** Company-specific constants and settings.

Can include: table names, default values, company-specific constants.

---

### 6.12 pipelines/{company}/models.py

**Purpose:** SQLAlchemy models for company-specific database tables.

Defines: Tables, columns, relationships for the company's data.

---

### 6.13 pipelines/{company}/tools/

**Purpose:** Company-specific tool implementations.

**Each tool:**
- Inherits from BaseTool
- Implements `name`, `description`, `parameters`
- Implements `execute(args, context)`
- Uses pipeline's database connections

---

### 6.14 pipelines/{company}/prompts/system_prompt.py

**Purpose:** Company-specific system prompt for the LLM agent.

**Contains:**
- Instructions for the LLM
- Description of available tools
- Output format requirements
- Company-specific rules

---

## 7. Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: REQUEST                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ POST /custom_rag/execute/                                       │
│ { function_id, prompt_objects, scope_variables, ... }           │
│                                                                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: VIEWS.PY                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ - Parse request                                                 │
│ - Extract function_id                                           │
│ - Call registry.get_pipeline()                                  │
│                                                                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: REGISTRY.PY                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ - Look up function_id in pipelines.json                         │
│ - Dynamic import pipeline class                                 │
│ - Build context                                                 │
│ - Return (pipeline_class, config, context)                      │
│                                                                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: PIPELINE.__ENTER__()                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ - Read database URL from os.getenv()                            │
│ - Create SQLAlchemy session                                     │
│ - Create Weaviate connection                                    │
│ - Load tools                                                    │
│                                                                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: PIPELINE.EXECUTE()                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ - Get system prompt                                             │
│ - Call agent_executor.execute()                                 │
│                                                                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: AGENT_EXECUTOR (Loop)                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Loop until final answer or max_iterations:                      │
│   - Send messages + tools to LLM                                │
│   - If tool_call → Execute tool → Add result → Continue         │
│   - If final_answer → Exit loop                                 │
│                                                                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: PIPELINE.__EXIT__()                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ALWAYS RUNS (even on error):                                    │
│ - Close SQLAlchemy session                                      │
│ - Dispose SQLAlchemy engine                                     │
│ - Close Weaviate connection                                     │
│ - Set all references to None                                    │
│                                                                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: RESPONSE                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ { success: true, output: {...}, metadata: {...} }               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Data Isolation

### 8.1 What Is Isolated Per Request

| Component | Isolated? | How |
|-----------|-----------|-----|
| Pipeline instance | Yes | Fresh instance per request |
| Context | Yes | Built from request data |
| Tools | Yes | Created per pipeline instance |
| SQLAlchemy session | Yes | New session per request |
| Weaviate connection | Yes | New connection per request |

### 8.2 Rules to Maintain Isolation

| Rule | Reason |
|------|--------|
| No global variables | Could leak between requests |
| No shared cache | Could return wrong company's data |
| No hardcoded values | Must read from config |
| Fresh connections per request | No connection reuse |
| Cleanup after every request | No state persists |

### 8.3 Isolation Guarantees

| Guarantee | How Achieved |
|-----------|--------------|
| Company A cannot see Company B data | Separate databases, separate Weaviate collections |
| Requests don't affect each other | Fresh instance per request |
| Failed request doesn't affect next | Cleanup always runs via context manager |
| No data leaks between requests | No global state, no shared cache |

---

## 9. Adding a New Pipeline

### 9.1 Step-by-Step Process

**Step 1: Copy Template**
```
cp -r pipelines/_template pipelines/{new_company}
```

**Step 2: Create SQLAlchemy Models**

Edit `models.py` with company-specific tables.

**Step 3: Edit config.py**

Define company-specific constants.

**Step 4: Edit pipeline.py**

- Update class name
- Implement `get_tools()`
- Implement `get_system_prompt()`

**Step 5: Create Tools**

Create tool files in `tools/` folder.

**Step 6: Create System Prompt**

Edit `prompts/system_prompt.py`.

**Step 7: Add to pipelines.json**

```
{
  "new_company_rag": {
    "pipeline": "custom_rag.pipelines.new_company.pipeline.RAGPipeline",
    "config": {
      "weaviate_collection": "NewCompanyProducts",
      "db_env_var": "NEW_COMPANY_DB_URL",
      "max_iterations": 10
    }
  }
}
```

**Step 8: Add Environment Variable**

Add database URL to environment:
```
NEW_COMPANY_DB_URL=mysql://user:pass@host:port/database
```

**Step 9: Set Up Databases**

- Create Weaviate collection
- Set up SQL database with required tables
- Populate with company data

**Step 10: Deploy**

No changes to core framework needed.

---

### 9.2 Pull Request Checklist

**Files to Include:**

| File | Check |
|------|-------|
| `pipelines/{company}/__init__.py` | ☐ |
| `pipelines/{company}/pipeline.py` | ☐ |
| `pipelines/{company}/config.py` | ☐ |
| `pipelines/{company}/models.py` | ☐ |
| `pipelines/{company}/tools/__init__.py` | ☐ |
| `pipelines/{company}/tools/*.py` | ☐ |
| `pipelines/{company}/prompts/__init__.py` | ☐ |
| `pipelines/{company}/prompts/system_prompt.py` | ☐ |
| `pipelines.json` (updated) | ☐ |

**Code Review Checks:**

| Check | Verify |
|-------|--------|
| No global variables | ☐ |
| No hardcoded database values | ☐ |
| All config from config dict | ☐ |
| All tools inherit from BaseTool | ☐ |
| Pipeline inherits from BasePipeline | ☐ |
| Proper cleanup in `__exit__` | ☐ |

**Config Checks:**

| Check | Verify |
|-------|--------|
| function_id is unique | ☐ |
| weaviate_collection is unique | ☐ |
| db_env_var is unique | ☐ |
| Pipeline path is correct | ☐ |

---

## 10. Summary Tables

### 10.1 Files and Responsibilities

| File | Responsibility | Shared/Specific |
|------|----------------|-----------------|
| urls.py | Route requests | Shared |
| views.py | Entry point, error handling | Shared |
| registry.py | Pipeline lookup, context building | Shared |
| pipelines.json | Configuration | Shared (entries per pipeline) |
| base_pipeline.py | Pipeline interface | Shared |
| base_tool.py | Tool interface | Shared |
| agent_executor.py | Agentic loop | Shared |
| database.py | SQLAlchemy wrapper | Shared |
| weaviate_connector.py | Weaviate wrapper | Shared |
| pipelines/{company}/pipeline.py | Pipeline implementation | Company-specific |
| pipelines/{company}/config.py | Configuration | Company-specific |
| pipelines/{company}/models.py | Database models | Company-specific |
| pipelines/{company}/tools/*.py | Tool implementations | Company-specific |
| pipelines/{company}/prompts/*.py | System prompt | Company-specific |

### 10.2 Request Data Flow

| Step | Data |
|------|------|
| Request | function_id, prompt_objects, scope_variables, previous_prompt_outputs, llm |
| Registry | Adds: pipeline_class, config |
| Pipeline | Adds: tools, system_prompt, connections |
| Agent | Uses all above, produces: output, iterations, tools_used |
| Response | success, output, metadata |

### 10.3 What Goes Where

| Data | Location | Reason |
|------|----------|--------|
| Pipeline mapping | pipelines.json | Easy to update, version control |
| Database credentials | Environment variables | Security |
| Company logic | pipelines/{company}/ | Isolated, maintainable |
| Shared logic | core/ | Reusable |

---

## 11. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | - | Initial version |