# MAF Agents - AI-Powered Detector Development

Automated ETW detector development workflow using Microsoft Agent Framework, Azure OpenAI, FastAPI, and Next.js.

> **Full-stack monorepo** with Python backend and Next.js frontend for conversational AI-powered detector development.

## 🚀 Quick Start

### Install All Dependencies

```bash
npm run install:all
```

Or using Make:
```bash
make install
```

### Configure Environment

```bash
# Server environment
cd server && cp .env.example .env
# Edit .env with your Azure credentials

# Client environment
cd ../client
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
echo "NEXT_PUBLIC_WS_URL=ws://localhost:8000" >> .env.local
```

### Run Both Servers

```bash
# From root directory
npm run dev
```

This starts:
- 🐍 **API Server** at `http://localhost:8000` (FastAPI + WebSocket)
- ⚛️  **Web UI** at `http://localhost:3000` (Next.js 15)

Or using Make:
```bash
make dev
```

## Overview

**maf-agents** automates the end-to-end Azure detector development lifecycle from ETW input to production promotion through a conversational, multi-agent workflow system. Built on Microsoft Agent Framework, the system orchestrates 9 specialized executors with checkpoint-based state management and human-in-the-loop approval gates.

## Goals

- Reduce detector development cycle time by 70% (from 6 hours to <2 hours)
- Achieve 90%+ code pattern consistency by learning from historical PR patterns
- Enable conversational, guided workflow with human oversight
- Successfully process 10+ detector workflows during POC phase

## Architecture

The system uses a **sequential workflow orchestration** pattern with:
- **8 Specialized Executors**: ETW Input, Schema Discovery, Code Generator, PR Creation, Approval Gate, Deployment Verification, Results Analysis, Production Promotion
- **Checkpoint-Based State Management**: File-based checkpoints for workflow recovery
- **Azure-Native Integrations**: Azure Repos for source control, Azure Kusto for data querying
- **Conversational Interface**: CLI-based interaction with progress feedback and step-by-step status updates

## 📁 Monorepo Structure

```
maf-agents/
├── server/             # Python backend (FastAPI + MAF)
│   ├── api/            # FastAPI REST/WebSocket server
│   ├── workflows/      # MAF workflow orchestration
│   ├── agents/         # Conversational AI agents
│   ├── shared/         # Shared utilities and models
│   ├── config/         # Configuration files
│   └── tests/          # Test suite
│
├── client/             # Next.js 15 frontend
│   ├── src/app/        # App Router pages
│   ├── src/components/ # React components (shadcn/ui)
│   ├── src/hooks/      # React hooks
│   └── src/lib/        # API client and utilities
│
├── docs/               # Documentation
├── package.json        # Monorepo scripts
└── Makefile            # Development commands
```

## 🛠️ Available Commands

### npm Scripts (Recommended)

```bash
npm run dev              # Run both server and client
npm run dev:server       # Run only API server
npm run dev:client       # Run only frontend
npm run build            # Build for production
npm run start            # Run both in production mode
npm run install:all      # Install all dependencies
npm run clean            # Clean build artifacts
```

### Makefile Commands

```bash
make dev                 # Run both servers
make dev-server          # Run only API server
make dev-client          # Run only frontend
make install             # Install all dependencies
make build               # Build for production
make clean               # Clean build artifacts
make test                # Run all tests
make help                # Show all available commands
```

## 🌐 URLs (When Running Locally)

- **Frontend**: http://localhost:3000
- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (OpenAPI/Swagger)
- **Health Check**: http://localhost:8000/health

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

### Basic Execution

```bash
# Start the detector development workflow
uv run python workflows/detector_workflow.py
```

### Workflow Steps

The workflow will execute 8 sequential steps:

**Step 1: ETW Input Collection [1/8]**
- Validates provider GUID and rule ID from input
- Example output: "✓ ETW Input validated: provider_guid=..., rule_id=..."

**Step 2: Schema Discovery [2/8]**
- Queries Kusto for ETW schema and existing detectors
- Example output: "✓ Schema discovered: 5 fields found"

**Step 3: Code Generator [3/8]**
- Analyzes historical PRs for patterns
- Generates detector code files
- Example output: "✓ Generated 3 files for detector"

**Step 4: PR Creation [4/8]**
- Creates branch: `detector/{rule_id}-{timestamp}`
- Commits code and creates PR in Azure Repos
- Example output: "✓ PR created: https://dev.azure.com/..."

**Step 5: Approval Gate [5/8]**
- Presents PR for user review
- Waits for explicit approval
- Example prompt: "Do you want to proceed with this PR? (yes/no):"

**Step 6: Deployment Verification [6/8]**
- Polls PR status every 30 seconds (exponential backoff)
- Verifies PR merge and deployment completion
- Example output: "✓ Deployment detected after 5 minutes"

**Step 7: Results Analysis [7/8]**
- Fetches detector results from Kusto
- Presents metrics and asks for confirmation
- Example output: "Events: 42, Error Rate: 0.5%, Do results look correct? (yes/no):"

**Step 8: Production Promotion [8/8]**
- Analyzes promotion patterns from historical PRs
- Creates promotion PR with feature flag configuration
- Example output: "✓ Promotion PR created: https://dev.azure.com/..."

### Environment Variables for Testing

```bash
# Automatically confirm results (skips manual approval in results analysis)
export MAF_AUTO_CONFIRM_RESULTS=true

# Run with auto-confirmation
uv run python workflows/detector_workflow.py
```

### Workflow Input Format

The workflow expects input in the following format:

```python
{
    "workflow_id": "unique-workflow-id",
    "provider_guid": "12345678-1234-1234-1234-123456789012",
    "rule_id": "my_detector_rule_name"
}
```

### Expected Duration

| Scenario | Expected Time |
|----------|--------------|
| Simple detector (3-5 fields) | 30-45 minutes |
| Medium detector (5-8 fields) | 45-60 minutes |
| Complex detector (8+ fields) | 60-90 minutes |
| Very complex (multi-event) | 90-120 minutes |

**Note**: Most time is spent waiting for PR merge and deployment (Step 6)

## Troubleshooting

### Common Issues

#### 1. Kusto Connection Timeout

**Symptom**: `KustoQueryException: Query execution exceeded timeout`

**Cause**: Query taking too long for high-volume data

**Solution**:
```python
# Increase timeout in shared/kusto_client.py
results = kusto_client.execute_query(query, timeout_seconds=60)
```

#### 2. Azure DevOps Authentication Failed

**Symptom**: `401 Unauthorized` when creating PRs

**Cause**: Invalid or expired service principal credentials

**Solution**:
1. Verify environment variables are set correctly
2. Check service principal has appropriate permissions:
   - Code: Read & Write
   - Pull Requests: Contribute
3. Regenerate credentials if expired

#### 3. Checkpoint File Permission Error

**Symptom**: `PermissionError: [Errno 13] Permission denied: './checkpoints'`

**Cause**: Checkpoint directory doesn't exist or lacks write permissions

**Solution**:
```bash
# Create checkpoint directory
mkdir -p checkpoints
chmod 755 checkpoints
```

#### 4. Pattern Matching Accuracy Low

**Symptom**: Generated code doesn't follow expected patterns

**Cause**: Insufficient historical PRs for pattern learning

**Solution**:
- Ensure repository has 30+ historical detector PRs
- Review pattern confidence scores in logs
- Manually adjust pattern thresholds if needed

#### 5. Deployment Detection Taking Too Long

**Symptom**: Workflow stuck at "Checking deployment status..."

**Cause**: PR not yet merged or deployment pipeline delayed

**Solution**:
- Verify PR is actually merged in Azure DevOps
- Check deployment pipeline status manually
- Increase polling timeout if pipelines are slow

#### 6. Results Analysis Fails

**Symptom**: "No results found" or empty results

**Cause**: Detector not generating events yet or Kusto query issue

**Solution**:
1. Verify detector is actually deployed and running
2. Check Kusto query template in `config/kusto_queries.yaml`
3. Manually run query in Kusto Explorer to debug
4. Adjust time range in query if needed

### Debugging Commands

```bash
# Check environment variables
env | grep AZURE

# Test Kusto connection
uv run python -c "from shared.kusto_client import create_kusto_client; print('Kusto OK')"

# Test Azure DevOps connection
uv run python -c "from shared.auth import get_auth_manager; print('Auth OK')"

# View checkpoint files
ls -la checkpoints/

# Check logs (if logging configured)
tail -f logs/workflow.log
```

### Getting Help

1. **Review Documentation**: Check [docs/](./docs/) for detailed guides
2. **Check Issues Log**: See [docs/poc-issues-log.md](./docs/poc-issues-log.md) for known issues
3. **Run Tests**: `uv run pytest tests/` to verify system health
4. **Enable Verbose Logging**: Set `MAF_LOG_LEVEL=DEBUG` for detailed logs

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

### Main Orchestrator (`workflows/detector_workflow.py`)
- Coordinates 8 sequential executors using MAF's `WorkflowBuilder`
- Manages checkpoint persistence using MAF's `FileCheckpointStorage`
- Provides CLI interface with formatted output and progress indicators
- Handles workflow streaming and event processing

### Executors (8-Step Sequential Workflow)
1. **ETW Input Collection** (`etw_input_collection_executor`): Validates and collects providerGuid and ruleId from workflow input
2. **Schema Discovery** (`schema_discovery_executor`): Queries Kusto to discover ETW schema and existing detectors
3. **Code Generator** (`code_generator_executor`): Analyzes historical PRs for patterns and generates detector code
4. **PR Creation** (`pr_creation_executor`): Creates Git branch, commits code, and creates pull request in Azure Repos
5. **Approval Gate** (`approval_gate_executor`): Human-in-the-loop approval using MAF's ChatAgent with `@ai_function` approval pattern
6. **Deployment Verification** (`deployment_verification_executor`): Polls PR status and verifies deployment completion with exponential backoff
7. **Results Analysis** (`results_analysis_executor`): Fetches detector results from Kusto and requests user confirmation
8. **Production Promotion** (`production_promotion_executor`): Analyzes promotion patterns and creates customer-facing PR

### Shared Utilities
- **Authentication** (`shared/auth.py`): Azure AD service principal authentication and Azure DevOps connection management
- **Checkpoint Storage** (MAF's `FileCheckpointStorage`): File-based state persistence for workflow recovery
- **Kusto Client** (`shared/kusto_client.py`): Kusto query execution with template support
- **Azure Repos Utils** (`shared/repos_utils.py`): Branch creation, file commits, and PR management

## Known Limitations (POC)

### POC Constraints

1. **Single Workflow Execution**: Only one detector workflow can run at a time (no parallel processing)
2. **Manual Configuration**: Kusto queries stored as static templates (no dynamic query generation)
3. **Limited Error Recovery**: Some transient failures require manual intervention
4. **CLI Interface Only**: No web UI or API endpoints
5. **File-Based Checkpoints**: Uses local filesystem (not production-ready for distributed systems)

### Out of Scope for POC

- Multi-detector batch processing
- Advanced error remediation with automated fixes
- Custom workflow configuration UI
- Real-time monitoring dashboards
- Automatic rollback on detector failures
- Support for non-ETW detector types
- Multi-language support (Python only)
- Performance optimization for large-scale queries

### Technical Debt

1. **Pattern Analyzer Requirements**: Needs 30+ historical PRs for >80% accuracy
2. **Azure API Rate Limiting**: No circuit breaker pattern implemented
3. **Connection Timeouts**: Long-running workflows may experience Kusto connection timeouts
4. **Error Messages**: Some error messages are too technical for end users
5. **Test Coverage**: Integration tests require Azure services (17 tests currently skipped)

**See [docs/poc-issues-log.md](./docs/poc-issues-log.md) for detailed issue tracking**

## Production Recommendations

### High Priority (Must Have for Production)

1. **Monitoring & Telemetry**: Application Insights integration for comprehensive logging
2. **Error Handling**: Implement retry with exponential backoff and circuit breaker patterns
3. **Pattern Management**: Periodic retraining of pattern analyzer (weekly/monthly)
4. **User Experience**: Real-time progress indicators and actionable error messages
5. **Performance**: Query result caching and connection pooling

### Medium Priority (Should Have)

6. **Security & Compliance**: Comprehensive audit logging and RBAC
7. **Scalability**: Azure Table Storage for checkpoints, workflow queue for concurrency
8. **Testing**: Expand integration test coverage for all edge cases
9. **Documentation**: Comprehensive user guide with troubleshooting

### Low Priority (Nice to Have)

10. **Advanced Features**: ML-based code generation, integration testing executor
11. **User Interface**: Web-based UI, Slack/Teams notifications

**See [docs/poc-validation-report.md](./docs/poc-validation-report.md) for complete analysis**

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
