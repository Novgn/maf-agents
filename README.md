# maf-agents

Multi-agent workflow system for Azure detector development using Microsoft Agent Framework (Python).

## Overview

**maf-agents** automates the end-to-end Azure detector development lifecycle from ETW input to production promotion through a conversational, multi-agent workflow system. Built on Microsoft Agent Framework, the system orchestrates 7 specialized agents with checkpoint-based state management and human-in-the-loop approval gates.

## Goals

- Reduce detector development cycle time by 70% (from 6 hours to <2 hours)
- Achieve 90%+ code pattern consistency by learning from historical PR patterns
- Enable conversational, guided workflow with human oversight
- Successfully process 10+ detector workflows during POC phase

## Architecture

The system uses a **sequential workflow orchestration** pattern with:
- **7 Specialized Agents**: ETW Input, Schema Discovery, Code Generator, Approval Gate, Deployment Verification, Results Analysis, Production Promotion
- **Checkpoint-Based State Management**: Azure Table Storage for workflow recovery
- **Azure-Native Integrations**: Azure Repos for source control, Azure Kusto for data querying
- **Conversational Interface**: CLI-based interaction with progress feedback

## Project Structure

```
maf-agents/
├── workflows/          # Main orchestrator and workflow definitions
├── agents/            # Individual sub-workflow agent implementations
├── shared/            # Common utilities (Kusto client, Azure DevOps SDK wrappers, auth)
├── tests/             # Unit and integration tests
├── config/            # Configuration files and Kusto query templates
├── docs/              # Documentation (PRD, architecture, stories)
└── pyproject.toml     # Project configuration and dependencies
```

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Azure subscription with:
  - Azure Repos (Azure DevOps) access
  - Azure Kusto (Data Explorer) cluster access
  - Azure Key Vault for secrets
  - Azure Table Storage for checkpoints

## Environment Setup

### 1. Install uv Package Manager

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Create Virtual Environment

```bash
# Install Python 3.11 (recommended)
uv python install 3.11

# Create virtual environment
uv venv --python 3.11

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all dependencies including dev tools
# Note: --prerelease=allow is required for Microsoft Agent Framework (preview)
uv sync --all-extras --prerelease=allow

# Or install only production dependencies
uv sync --prerelease=allow
```

### 4. Install Pre-commit Hooks (Optional)

```bash
uv run poe pre-commit-install
```

## Configuration

### Azure Service Principal

Create a service principal with appropriate permissions:

```bash
az ad sp create-for-rbac --name maf-agents-poc \
  --role Contributor \
  --scopes /subscriptions/{subscription-id}
```

Store credentials in Azure Key Vault:
- `tenant-id`
- `client-id`
- `client-secret`

### Environment Variables

Create a `.env` file in the project root:

```env
# Azure Authentication
AZURE_KEY_VAULT_URL=https://{your-vault}.vault.azure.net/

# Azure Kusto
KUSTO_CLUSTER_URL=https://{cluster}.{region}.kusto.windows.net
KUSTO_DATABASE_NAME={database}

# Azure DevOps / Azure Repos
AZURE_DEVOPS_ORG=https://dev.azure.com/{organization}
AZURE_DEVOPS_PROJECT={project}
AZURE_DEVOPS_REPO={repository}

# Azure Table Storage
AZURE_STORAGE_CONNECTION_STRING={connection-string}
CHECKPOINT_TABLE_NAME=workflowcheckpoints
```

### Kusto Query Templates

Kusto queries are stored as templates in `config/kusto_queries.yaml` for easy modification without code changes.

#### Available Templates

- `find_existing_detectors` - Find detectors for a provider GUID
- `get_etw_schema` - Retrieve ETW schema fields
- `fetch_detector_results` - Fetch detector results for analysis
- `get_detector_stats` - Get detector execution statistics
- `find_similar_detectors` - Find detectors with similar providers

#### Using Templates

```python
from shared.kusto_client import create_kusto_client

# Create client
kusto_client = create_kusto_client(cluster_url, database, auth_manager)

# Load and execute template
query = kusto_client.load_query_template(
    "get_etw_schema",
    {"provider_guid": "12345678-1234-1234-1234-123456789012"}
)
results = kusto_client.execute_query(query)
```

#### Adding New Templates

1. Edit `config/kusto_queries.yaml`
2. Add your template with descriptive name:

```yaml
my_new_query: |
  // Query description
  MyTable
  | where Column == '{parameter}'
  | project Field1, Field2
```

3. Use placeholders with `{parameter_name}` syntax
4. Document required parameters in comments
5. Test with `load_query_template()` method

## Development Commands

```bash
# Run linting
uv run poe lint

# Run formatting
uv run poe format

# Run type checking
uv run poe type-check

# Run tests
uv run poe test

# Run tests with coverage
uv run poe test-cov

# Run all checks (lint, format, type-check, test)
uv run poe all-checks
```

## Running the Workflow

```bash
# Start the detector development workflow
uv run python workflows/detector_workflow.py
```

## Testing

### Unit Tests

```bash
# Run all unit tests
uv run pytest tests/unit/

# Run specific test file
uv run pytest tests/unit/test_checkpoint.py
```

### Integration Tests

```bash
# Run all integration tests
uv run pytest tests/integration/

# Run end-to-end workflow test
uv run pytest tests/integration/test_e2e_workflow.py
```

## Technology Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Package Management | uv | Latest | Fast dependency management |
| Task Automation | poethepoet | Latest | Dev task runner |
| Linting & Formatting | ruff | Latest | Code quality (120-char lines) |
| Type Checking | pyright + mypy | Latest | Static type analysis |
| Testing | pytest | 7.4+ | Unit and integration tests |
| Agent Framework | Microsoft Agent Framework | Latest | Workflow orchestration |
| Azure SDKs | azure-* | Latest | Azure service integration |

## Key Components

### Main Orchestrator
- Coordinates 7 sequential agents
- Manages checkpoint persistence
- Provides conversational CLI interface

### Agents
1. **ETW Input Collection**: Gather providerGuid and ruleId
2. **Schema Discovery**: Query Kusto for ETW schema
3. **Code Generator**: Generate detector code from patterns
4. **PR Creation**: Create branch and submit PR
5. **Approval Gate**: Human-in-the-loop checkpoint
6. **Deployment Verification**: Monitor PR merge and deployment
7. **Results Analysis**: Query and analyze detector results
8. **Production Promotion**: Create promotion PR

### Shared Utilities
- **Authentication**: Azure AD service principal auth
- **Checkpoint Manager**: State persistence to Azure Table Storage
- **Kusto Client**: Query execution wrapper
- **Azure Repos Client**: PR and branch management wrapper

## POC Success Criteria

- ✅ Complete workflow execution in <2 hours (70% reduction from 6 hours)
- ✅ 80%+ code pattern matching accuracy
- ✅ Checkpoint recovery reliability
- ✅ User satisfaction rating 4/5 or higher
- ✅ 10+ successful detector workflows

## Documentation

- [Project Brief](docs/brief.md)
- [Product Requirements Document (PRD)](docs/prd.md)
- [Architecture Document](docs/architecture.md)
- [User Stories](docs/stories/)

## Contributing

This is a POC project. For development workflow:

### ⚠️ IMPORTANT: Documentation-First Development

**ALWAYS review official documentation BEFORE implementing any feature:**

1. **Read Microsoft Agent Framework docs** at https://learn.microsoft.com/en-us/agent-framework/
2. **Review code samples** for the specific pattern you need
3. **Follow MAF patterns exactly** - do not create custom implementations
4. **Ask "Does MAF already provide this?"** before writing custom code

**Common Mistakes to Avoid:**
- ❌ Creating custom "agent" wrapper classes → Use `@executor` decorator
- ❌ Building custom orchestration logic → Use `WorkflowBuilder`
- ❌ Wrapping Azure SDKs → Use them directly in executors
- ❌ Assuming you need custom code → MAF likely has a built-in pattern

**See [MAF_BEST_PRACTICES.md](./MAF_BEST_PRACTICES.md) for detailed guidance.**

### Development Standards

1. Follow Microsoft Agent Framework development standards
2. All code must pass linting, formatting, type checking, and tests
3. Maintain 80%+ test coverage
4. Update documentation for significant changes

## License

Internal POC - Not for public distribution

## Support

For questions or issues during POC phase, contact the project team.
