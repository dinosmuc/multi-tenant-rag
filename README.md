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
