# MAF Agents - Server

Python backend for the MAF Agents workflow system, providing detector development workflows and FastAPI endpoints for the frontend.

## Structure

```
server/
├── agents/           # Conversational agents
├── workflows/        # Workflow orchestration
├── shared/           # Shared utilities and models
├── config/           # Configuration management
├── api/              # FastAPI REST/WebSocket server
└── tests/            # Test suite
```

## Quick Start

### Install Dependencies

```bash
# Using uv (recommended)
uv sync --all-extras

# Or using pip
pip install -e ".[dev]"
```

### Run API Server

```bash
# Using poe
poe api

# Or directly
cd server
uvicorn api.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Run Standalone Workflow

```bash
# Using poe
poe workflow

# Or directly
python workflows/detector_workflow.py
```

## API Endpoints

### REST Endpoints

- `POST /api/workflows` - Create new workflow
- `GET /api/workflows` - List all workflows
- `GET /api/workflows/{id}` - Get workflow status
- `POST /api/workflows/{id}/input` - Submit user input
- `DELETE /api/workflows/{id}` - Delete workflow

### WebSocket

- `WS /ws/workflows/{id}` - Real-time workflow updates

## Development

### Run Tests

```bash
poe test

# With coverage
poe test-cov
```

### Code Quality

```bash
# Lint
poe lint

# Format
poe format

# Type check
poe type-check

# All checks
poe all-checks
```

## Environment Variables

Create a `.env` file in the `server/` directory:

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4

# Azure Kusto
KUSTO_CLUSTER_URL=https://your-cluster.kusto.windows.net
KUSTO_DATABASE_NAME=your-database

# Azure DevOps
AZURE_DEVOPS_ORG=https://dev.azure.com/your-org
AZURE_DEVOPS_PROJECT=your-project
AZURE_DEVOPS_REPO=your-repo

# Azure Storage (for checkpoints)
AZURE_STORAGE_CONNECTION_STRING=...
CHECKPOINT_TABLE_NAME=workflowcheckpoints

# Logging
LOG_LEVEL=INFO
```

## Workflow Steps

The detector development workflow consists of 9 steps:

1. **Detector Triage** - Conversational requirements gathering
2. **ETW Input** - Collect provider GUID and rule ID
3. **Schema Discovery** - Query Kusto for ETW schema
4. **Code Generator** - Generate detector code
5. **PR Creation** - Create branch and pull request
6. **Approval Gate** - Human review and approval
7. **Deployment Verification** - Monitor PR merge
8. **Results Analysis** - Analyze detector effectiveness
9. **Production Promotion** - Promote to production

## Architecture

The server uses:

- **Microsoft Agent Framework (MAF)** - For workflow orchestration and conversational agents
- **FastAPI** - For REST and WebSocket APIs
- **Azure OpenAI** - For LLM-powered agents
- **Azure Kusto** - For schema discovery and results analysis
- **Azure DevOps** - For PR management
