# MAF Agents - Monorepo

AI-powered detector development workflow system using Microsoft Agent Framework, FastAPI, and Next.js.

## 📁 Repository Structure

```
maf-agents/
├── server/              # Python backend (FastAPI + MAF)
│   ├── agents/          # Conversational AI agents
│   ├── workflows/       # MAF workflow orchestration
│   ├── shared/          # Shared utilities and models
│   ├── config/          # Configuration management
│   ├── api/             # FastAPI REST/WebSocket server
│   └── tests/           # Test suite
│
├── client/              # Next.js 15 frontend
│   ├── src/
│   │   ├── app/         # Next.js App Router pages
│   │   ├── components/  # React components (shadcn/ui)
│   │   ├── hooks/       # React hooks
│   │   └── lib/         # Utilities and API client
│   └── public/          # Static assets
│
└── docs/                # Documentation
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (with `uv` package manager recommended)
- **Node.js 18+** and **npm**
- **Azure OpenAI** access
- **Azure DevOps** and **Kusto** (optional, for full functionality)

### One-Command Setup (Recommended)

```bash
# Install all dependencies
npm run install:all

# Or using make
make install
```

### Configure Environment

```bash
# Server environment
cd server
cp .env.example .env
# Edit .env with your Azure credentials

# Client environment
cd ../client
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
echo "NEXT_PUBLIC_WS_URL=ws://localhost:8000" >> .env.local
```

### Run Both Servers Simultaneously

**Option 1: Using npm scripts (Recommended)**
```bash
# From the root directory
npm run dev
```

This will run:
- 🐍 API server on `http://localhost:8000`
- ⚛️  Next.js UI on `http://localhost:3000`

**Option 2: Using Makefile**
```bash
make dev
```

**Option 3: Manual (separate terminals)**

Terminal 1 (Server):
```bash
cd server
uv run uvicorn api.main:app --reload --port 8000
```

Terminal 2 (Client):
```bash
cd client
npm run dev
```

### Available Commands

**npm scripts:**
- `npm run dev` - Run both servers in development mode
- `npm run dev:server` - Run only the API server
- `npm run dev:client` - Run only the frontend
- `npm run build` - Build client for production
- `npm run start` - Run both in production mode
- `npm run install:all` - Install all dependencies
- `npm run clean` - Clean all build artifacts

**Makefile commands:**
- `make dev` - Run both servers
- `make dev-server` - Run only API server
- `make dev-client` - Run only frontend
- `make install` - Install all dependencies
- `make build` - Build for production
- `make clean` - Clean build artifacts
- `make test` - Run all tests
- `make help` - Show all available commands

## 🏗️ Architecture

### Backend (Python + FastAPI)

**Technology Stack:**
- **Microsoft Agent Framework (MAF)**: Workflow orchestration and conversational agents
- **FastAPI**: REST and WebSocket APIs
- **Azure OpenAI**: LLM-powered agents
- **Azure Kusto**: Schema discovery and results analysis
- **Azure DevOps**: PR management

**Key Components:**

1. **Agents** (`server/agents/`):
   - `detector_triage_agent.py` - Requirements gathering
   - `etw_input_agent.py` - ETW input validation
   - `schema_discovery_agent.py` - Kusto schema queries
   - `pattern_analysis_agent.py` - PR pattern analysis
   - `code_generator_agent.py` - Detector code generation

2. **Workflows** (`server/workflows/`):
   - `detector_workflow.py` - 9-step detector development pipeline

3. **API** (`server/api/`):
   - `main.py` - FastAPI server with REST and WebSocket endpoints

### Frontend (Next.js 15 + React)

**Technology Stack:**
- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **shadcn/ui**: Beautiful, accessible components
- **WebSocket**: Real-time workflow updates

**Key Components:**

1. **Pages** (`client/src/app/`):
   - `/workflow` - Main workflow interface

2. **Components** (`client/src/components/`):
   - `workflow-stepper.tsx` - Visual progress indicator
   - `ui/` - shadcn/ui components (button, card, dialog, etc.)

3. **Hooks** (`client/src/hooks/`):
   - `use-workflow.ts` - Workflow state management

4. **API Client** (`client/src/lib/`):
   - `api-client.ts` - REST and WebSocket client

## 📊 Workflow Steps

The detector development workflow consists of 9 automated steps:

1. **Detector Triage** - Conversational requirements gathering
2. **ETW Input** - Collect provider GUID and rule ID
3. **Schema Discovery** - Query Kusto for ETW schema
4. **Code Generation** - Generate detector code using AI
5. **PR Creation** - Create branch and pull request
6. **Approval Gate** - Human review and approval
7. **Deployment Verification** - Monitor PR merge
8. **Results Analysis** - Analyze detector effectiveness
9. **Production Promotion** - Promote to production

## 🔌 API Endpoints

### REST Endpoints

- `POST /api/workflows` - Create new workflow
- `GET /api/workflows` - List all workflows
- `GET /api/workflows/{id}` - Get workflow status
- `POST /api/workflows/{id}/input` - Submit user input
- `DELETE /api/workflows/{id}` - Delete workflow
- `GET /health` - Health check

### WebSocket

- `WS /ws/workflows/{id}` - Real-time workflow updates

Example WebSocket message:
```json
{
  "type": "workflow_update",
  "workflow_id": "abc123",
  "status": "running",
  "step_number": 3,
  "current_step": "schema_discovery",
  "data": {...}
}
```

## 🧪 Development

### Running Tests

```bash
cd server
uv run poe test

# With coverage
uv run poe test-cov
```

### Code Quality

```bash
cd server

# Lint
uv run poe lint

# Format
uv run poe format

# Type check
uv run poe type-check
```

### Frontend Development

```bash
cd client

# Lint
npm run lint

# Build
npm run build

# Production server
npm run start
```

## 🌐 Environment Variables

### Server (`.env`)

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

### Client (`.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## 📖 Documentation

- **Server README**: `server/README.md`
- **Client README**: `client/README.md`
- **MAF Best Practices**: `MAF_BEST_PRACTICES.md`
- **Contributing Guide**: `CONTRIBUTING.md`

## 🤝 Contributing

1. Follow the code style guidelines in `CONTRIBUTING.md`
2. Write tests for new features
3. Update documentation
4. Submit pull requests with clear descriptions

## 📄 License

[Your License Here]

## 🙋 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/your-org/maf-agents/issues)
- **Documentation**: [Full docs](./docs/)
- **API Docs**: Visit `http://localhost:8000/docs` when server is running

## 🎯 Roadmap

- [ ] Add more detector types beyond ETW
- [ ] Implement user authentication
- [ ] Add workflow templates
- [ ] Build admin dashboard
- [ ] Add metrics and analytics
- [ ] Support multiple Azure tenants
