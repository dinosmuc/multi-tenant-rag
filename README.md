# Custom RAG Pipeline System

A RAG (Retrieval-Augmented Generation) pipeline system for the BlueCallom platform.

## Prerequisites

Before you start, make sure you have:

- **Python 3.11 or higher** installed
- **pip** (comes with Python)
- **Git**
- **OpenAI API key** (get one from https://platform.openai.com/)
- **Weaviate Cloud account** (sign up at https://console.weaviate.cloud/)
- **Database connection** (MySQL or PostgreSQL - get credentials from your team)

## How to Run

### Step 1: Clone the repository

```bash
git clone <repository-url>
cd custom-rag
```

### Step 2: Create virtual environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux
```

### Step 3: Install dependencies

```bash
pip install -r requirements-dev.txt
```

### Step 4: Set up environment variables

**Copy the template file:**
```bash
copy .env.example .env         # Windows
cp .env.example .env           # macOS/Linux
```

**Generate a Django secret key:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Open `.env` file and fill in these values:**

```env
# Django Settings
SECRET_KEY=paste-the-generated-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# OpenAI API (REQUIRED)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Weaviate Vector Database (REQUIRED)
WEAVIATE_URL=https://your-cluster.weaviate.network
WEAVIATE_API_KEY=your-weaviate-api-key

# Company Database (REQUIRED)
COMPANY_1_DB_URL=mysql://user:password@host:port/blccoredemo
```

> **Where to get these values?**
> - **OpenAI API Key**: Get from https://platform.openai.com/api-keys
> - **Weaviate URL & API Key**: Get from your Weaviate Cloud dashboard at https://console.weaviate.cloud/
> - **Database URL**: Ask your team lead for database credentials

### Step 5: Run Django migrations

```bash
python manage.py migrate
```

### Step 6: Start the server

```bash
python manage.py runserver
```

The server will start at: **http://localhost:8000/**

✅ **You're ready!** The API endpoint is available at: `http://localhost:8000/custom_rag/execute/`

## Running Tests

Make sure your virtual environment is activated, then run:

```bash
pytest
```

All tests should pass (18 tests total).

## Code Quality

Before committing your changes, run these commands:

```bash
# Format your code
black .

# Check for issues
ruff check --fix .

# Run tests
pytest
```

## How to Use the API

Once the server is running, you can send requests to the API.

### Example Request

Use **Postman**, **cURL**, or any HTTP client:

```bash
curl -X POST http://localhost:8000/custom_rag/execute/ \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "company_1",
    "llm_provider": "openai",
    "llm": "gpt-4o",
    "prompt_objects": {
      "query": "Show me SAP products for mid-market customers"
    }
  }'
```

**Request Parameters:**
- `function_id` - Which pipeline to use (e.g., `"company_1"`)
- `llm_provider` - AI provider (currently `"openai"`)
- `llm` - Model name (e.g., `"gpt-4o"`, `"gpt-4o-mini"`, `"o1-preview"`)
- `reasoning_effort` - Optional, for resoning models only (`"low"`, `"medium"`, `"high"`)
- `prompt_objects` - Your input data (e.g., `{"query": "your question"}`)

### Example Response

```json
{
  "success": true,
  "data": {
    "output": "Here are the SAP products for mid-market customers: ...",
    "iterations": 5,
    "tools_used": ["semantic_search", "sql_query"]
  },
  "usage": {
    "input_tokens": 1234,
    "output_tokens": 567,
    "total_tokens": 1801
  }
}
```

## Troubleshooting

**Issue: "ModuleNotFoundError"**
- Make sure your virtual environment is activated
- Run `pip install -r requirements-dev.txt` again

**Issue: "Database connection error"**
- Check your `COMPANY_1_DB_URL` in `.env` file
- Verify you have the correct database credentials
- Make sure the database server is accessible

**Issue: "Weaviate connection error"**
- Check your `WEAVIATE_URL` and `WEAVIATE_API_KEY` in `.env`
- Verify your Weaviate cluster is running
- Check your internet connection

**Issue: "OpenAI API error"**
- Verify your `OPENAI_API_KEY` is correct
- Check you have credits in your OpenAI account
- Make sure the API key has the correct permissions

## Need Help?

- Check `CLAUDE.md` for detailed technical documentation
- Check `project.md` for architecture and design details
- Ask your team lead for credentials or access issues
- Contact the development team for other questions

---

## Implementing a New Pipeline

This guide walks you through creating a new custom RAG pipeline step by step, using the existing Company 1 pipeline as a reference.

### Pipeline Structure Overview

A complete pipeline consists of:
- **Pipeline Class** - Main orchestration logic
- **Models** - Database schema definitions (SQLAlchemy ORM)
- **Tools** - Individual functions the AI agent can call
- **Prompts** - System and planning prompts for the AI agent
- **Configuration** - Pipeline registration and settings

### Step 1: Create Pipeline Directory Structure

Create a new directory under `custom_rag/pipelines/` for your pipeline:

```bash
mkdir -p custom_rag/pipelines/your_company/
mkdir -p custom_rag/pipelines/your_company/tools/
mkdir -p custom_rag/pipelines/your_company/prompts/
```

Your directory structure should look like:
```
custom_rag/pipelines/your_company/
├── __init__.py
├── pipeline.py          # Main pipeline class
├── models.py           # Database models
├── prompts/
│   ├── __init__.py
│   ├── system_prompt.py    # AI agent instructions
│   └── planning_prompt.py  # Planning instructions
└── tools/
    ├── __init__.py
    ├── tool1.py           # Individual tools
    ├── tool2.py
    └── ...
```

### Step 2: Create Database Models

Create `models.py` with your database schema using SQLAlchemy ORM:

```python
"""SQLAlchemy ORM models for YourCompany database schema."""

from sqlalchemy import DECIMAL, JSON, Boolean, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class YourMainTable(Base):
    """Main table for your domain."""
    
    __tablename__ = "your_main_table"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    # Add your specific fields here
    description = Column(Text)
    metadata_field = Column(JSON)
    # ... more fields

class YourSupportingTable(Base):
    """Supporting table with relationships."""
    
    __tablename__ = "your_supporting_table"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    main_table_id = Column(String(50), nullable=False)
    # Add your specific fields here
```

### Step 3: Create Individual Tools

Each tool should inherit from `BaseTool` and implement the required methods. Here's a template:

```python
"""Tool for [specific functionality]."""

from typing import Any
from custom_rag.core.base_tool import BaseTool
from custom_rag.pipelines.your_company.models import YourMainTable

class YourCustomTool(BaseTool):
    """Tool description for the AI agent."""

    @property
    def name(self) -> str:
        return "your_tool_name"

    @property
    def description(self) -> str:
        return """Clear description of what this tool does.
        Explain when the AI should use it and what it returns."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "parameter_name": {
                    "type": "string",
                    "description": "Description of this parameter",
                },
                "optional_param": {
                    "type": "integer", 
                    "description": "Optional parameter",
                    "default": 10,
                }
            },
            "required": ["parameter_name"],
        }

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        """Execute the tool logic."""
        db = context.get("db")
        if not db:
            return {"error": "Database connection not available"}
            
        # Get parameters
        param = args.get("parameter_name")
        
        try:
            session = db.get_session()
            
            # Your tool logic here
            # Query database, process data, etc.
            
            session.close()
            return {"result": "your_result"}
            
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
```

**Common Tool Patterns:**
- **Search Tools** - Find items using semantic search or database queries
- **Detail Tools** - Get comprehensive information about specific items
- **Analysis Tools** - Process and analyze data
- **Output Tools** - Format final responses (always include one)

### Step 4: Create System Prompt

Create `prompts/system_prompt.py` with detailed instructions for your AI agent:

```python
"""System prompt for YourCompany RAG agent."""

SYSTEM_PROMPT = """You are an intelligent assistant with access to [YourCompany]'s [domain] information.

Your role is to fulfill queries about [your domain] by using the available tools to search, analyze, and provide comprehensive answers.

═══════════════════════════════════════════════════════════════════════════════
DATABASE SCHEMAS
═══════════════════════════════════════════════════════════════════════════════

## SQL DATABASE

**Database Name:** your_database_name
**Architecture:** [Describe your schema architecture]

### Table 1: `your_main_table`
Description of what this table contains.

**Core Fields:**
- `id` (VARCHAR(50), PRIMARY KEY) - Description
- `name` (VARCHAR(255)) - Description
- ... [Document all important fields]

### Table 2: `your_supporting_table`
Description of relationships and purpose.

═══════════════════════════════════════════════════════════════════════════════
VECTOR DATABASE
═══════════════════════════════════════════════════════════════════════════════

**Collection:** YourCompanyCollection
**Content:** [Describe what's indexed in vector search]

═══════════════════════════════════════════════════════════════════════════════
TOOL USAGE GUIDELINES
═══════════════════════════════════════════════════════════════════════════════

[Provide specific guidance on how to use your tools effectively]

1. **Initial Search**: Start with semantic_search for discovery
2. **Get Details**: Use detail tools for comprehensive information
3. **Analysis**: Apply analysis tools as needed
4. **Final Answer**: Always use create_final_answer to conclude

═══════════════════════════════════════════════════════════════════════════════
RESPONSE GUIDELINES
═══════════════════════════════════════════════════════════════════════════════

- Always provide complete, actionable answers
- Include relevant details and context
- Structure responses clearly with sections
- Cite specific data sources when possible
"""
```

### Step 5: Create Planning Prompt

Create `prompts/planning_prompt.py`:

```python
"""Planning prompt for YourCompany RAG agent."""

PLANNING_PROMPT = """You are a planning assistant for [YourCompany] [domain] RAG system.

Your job is to create a step-by-step execution plan for answering user queries.

AVAILABLE TOOLS:
- your_search_tool: Description of when to use
- your_detail_tool: Description of when to use  
- your_analysis_tool: Description of when to use
- create_final_answer: Write and return complete answer (REQUIRED to finish)

DATABASE CONTEXT:
- SQL database with [list your tables]
- Weaviate vector database for semantic search

OUTPUT FORMAT:
Create a numbered execution plan. Each step should specify:
- What to do
- Which tool to use
- What information to gather

Keep the plan focused (3-7 steps typically). Always end with create_final_answer."""
```

### Step 6: Create Main Pipeline Class

Create `pipeline.py` with your main pipeline orchestration:

```python
"""YourCompany RAG pipeline implementation."""

import logging
from typing import Any

from custom_rag.core.agent_executor import AgentExecutor
from custom_rag.core.base_pipeline import BasePipeline
from custom_rag.core.base_tool import BaseTool
from custom_rag.pipelines.your_company.prompts.planning_prompt import PLANNING_PROMPT
from custom_rag.pipelines.your_company.prompts.system_prompt import SYSTEM_PROMPT
from custom_rag.pipelines.your_company.tools.your_tool1 import YourTool1
from custom_rag.pipelines.your_company.tools.your_tool2 import YourTool2
# Import all your tools

logger = logging.getLogger(__name__)

class YourCompanyPipeline(BasePipeline):
    """
    YourCompany [domain] RAG pipeline.
    
    [Describe what this pipeline does and its main use cases]
    """

    def get_tools(self) -> list[BaseTool]:
        """Return all available tools for this pipeline."""
        return [
            YourTool1(),
            YourTool2(),
            # List all your tools
        ]

    def get_system_prompt(self) -> str:
        """Return system prompt with DB schemas and instructions."""
        return SYSTEM_PROMPT

    def get_planning_prompt(self) -> str:
        """Return planning prompt with execution planning instructions."""
        return PLANNING_PROMPT

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the pipeline with agentic loop."""
        query = context.get("prompt_objects", {}).get("query", "")

        logger.info(f"🎯 YOURCOMPANY PIPELINE STARTED: {query}")
        
        # Add db and weaviate connections to context
        context["db"] = self.db
        context["weaviate"] = self.weaviate

        # Get LLM provider from context
        llm_provider = context.get("llm_provider")
        if not llm_provider:
            logger.error("LLM provider not available in context")
            return {
                "output": {"error": "LLM provider not available in context"},
                "iterations": 0,
                "tools_used": [],
            }

        # Create agent executor
        agent_executor = AgentExecutor(
            tools=self.tools,
            system_prompt=self.get_system_prompt(),
            planning_prompt=self.get_planning_prompt(),
            llm_provider=llm_provider,
            max_iterations=self.config.get("max_iterations", 100),
        )

        # Execute agentic loop
        result = agent_executor.execute(context)

        # Return results
        final_answer = context.get("final_answer", result.get("output"))
        return {
            "output": final_answer,
            "iterations": result.get("iterations", 0),
            "tools_used": result.get("tools_used", []),
            "usage": result.get("usage", {}),
        }
```

### Step 7: Register Your Pipeline

Add your pipeline to `custom_rag/pipelines.json`:

```json
{
  "company_1": {
    "pipeline": "custom_rag.pipelines.company_1.pipeline.Company1Pipeline",
    "config": {
      "weaviate_collection": "Company1Products",
      "db_env_var": "COMPANY_1_DB_URL",
      "max_iterations": 100
    }
  },
  "your_company": {
    "pipeline": "custom_rag.pipelines.your_company.pipeline.YourCompanyPipeline",
    "config": {
      "weaviate_collection": "YourCompanyCollection",
      "db_env_var": "YOUR_COMPANY_DB_URL",
      "max_iterations": 100
    }
  }
}
```

### Step 8: Set Up Environment Variables

Add your database connection to `.env`:

```bash
# Your Company Database
YOUR_COMPANY_DB_URL=mysql://user:password@host:port/database_name
```

### Step 9: Test Your Pipeline

Create a test API call to verify your pipeline works:

```bash
curl -X POST http://localhost:8000/api/execute-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "your_company",
    "llm_provider": "openai",
    "llm": "gpt-4o",
    "prompt_objects": {
      "query": "Your test query here"
    }
  }'
```

### Step 10: Essential Tool Implementation Tips

**1. Always Include a Final Answer Tool:**
```python
class CreateFinalAnswerTool(BaseTool):
    """Create and store the final formatted answer."""
    
    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
        answer = args.get("answer", "")
        context["final_answer"] = answer  # Store in context
        return {"status": "Answer created and stored successfully"}
```

**2. Implement Error Handling:**
```python
def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
    try:
        # Tool logic here
        return {"result": result}
    except Exception as e:
        logger.error(f"Tool {self.name} failed: {str(e)}")
        return {"error": f"Tool execution failed: {str(e)}"}
```

**3. Use Logging for Debugging:**
```python
import logging
logger = logging.getLogger(__name__)

def execute(self, args: dict[str, Any], context: dict[str, Any]) -> Any:
    logger.info(f"Executing {self.name} with args: {args}")
    # ... tool logic
    logger.info(f"Tool {self.name} completed successfully")
```

### Calling Your Pipeline

Once implemented, your pipeline can be called via the API:

**Endpoint:** `POST /api/execute-pipeline`

**Request Format:**
```json
{
  "function_id": "your_company",
  "llm_provider": "openai",
  "llm": "gpt-4o",
  "prompt_objects": {
    "query": "Your user query here"
  },
  "scope_variables": {},
  "previous_prompt_outputs": {}
}
```

**Response Format:**
```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "output": "Generated answer",
    "metadata": {
      "iterations": 5,
      "tools_used": ["tool1", "tool2", "tool3"]
    }
  },
  "usage": {
    "input_tokens": 1500,
    "output_tokens": 800,
    "total_tokens": 2300
  }
}
```

### Best Practices

1. **Start Simple** - Begin with 3-5 core tools, expand later
2. **Clear Documentation** - Document all database fields and tool purposes
3. **Error Handling** - Always handle database/API failures gracefully
4. **Logging** - Add comprehensive logging for debugging
5. **Testing** - Test each tool individually before integration
6. **Performance** - Consider database query optimization and caching
7. **Security** - Validate all inputs and sanitize database queries

This guide provides the complete blueprint for implementing a new RAG pipeline. Use the Company 1 pipeline as your reference implementation, and adapt the patterns to your specific domain and requirements.
