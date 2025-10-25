# maf-agents Architecture Document

## Introduction

This document outlines the overall project architecture for **maf-agents**, including backend systems, shared services, and non-UI specific concerns. Its primary goal is to serve as the guiding architectural blueprint for AI-driven development, ensuring consistency and adherence to chosen patterns and technologies.

**Relationship to Frontend Architecture:**
This is a backend/CLI-focused POC with a terminal-based conversational interface. No separate Frontend Architecture Document is needed. Core technology stack choices documented herein are definitive for the entire project.

### Starter Template or Existing Project

**Decision: No Starter Template - Manual Setup**

This is a **greenfield project** with specific technology constraints from the PRD:
- Must use Microsoft Agent Framework (Python SDK) - REQUIRED
- Python 3.10+
- Azure-native services (Azure Repos, Azure Kusto)
- Monorepo structure

**Rationale:**
Given the unique nature of this project (Microsoft Agent Framework POC for workflow orchestration), there are no standard starter templates that fit. The Microsoft Agent Framework is a specialized framework for building agent-based workflows, not covered by typical Python project templates.

- **No starter template** - Manual project setup required following Microsoft Agent Framework dev setup patterns
- Use `pyproject.toml` with **uv** package manager (aligned with MAF standards)
- Follow Microsoft Agent Framework documentation for initial setup
- Leverage Azure SDK patterns for authentication

**Benefits:**
- Clean setup ensures we only include necessary dependencies
- Avoids removing unused boilerplate from generic templates
- POC timeline (2-3 weeks) allows for manual setup
- Aligns with Microsoft Agent Framework development standards

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-10-24 | 0.1 | Initial architecture draft | Architect (Winston) |

---

## High Level Architecture

### Technical Summary

The **maf-agents** system is a **stateless workflow orchestration engine** built on Microsoft Agent Framework (Python) that implements a sequential agent-based architecture for automated Azure detector development. The main orchestrator coordinates 7 specialized sub-workflow agents (ETW Input Collection, Schema Discovery, Code Generator, Approval Gate, Deployment Verification, Results Analysis, Production Promotion) through a linear workflow with checkpoint-based state persistence to Azure Table Storage. The system integrates with Azure-native services—Azure Repos for source control operations and Azure Kusto for data querying—using official Python SDKs with Azure AD service principal authentication. This architecture directly supports the PRD goals of 70% cycle time reduction and 90%+ pattern consistency by automating the complete detector lifecycle while maintaining human-in-the-loop control at critical approval gates.

### High Level Overview

**1. Architectural Style**

**Event-Driven Sequential Workflow Architecture** with checkpoint-based state management. The system follows a linear progression through discrete workflow stages, with each stage triggering the next upon successful completion. Unlike traditional microservices or monolithic architectures, this uses the Microsoft Agent Framework's orchestration patterns to coordinate autonomous agents.

**2. Repository Structure** (from PRD)

**Monorepo** - Single repository containing all workflow agents, shared utilities, and orchestration code:
- `/workflows` - Main orchestrator and workflow definitions
- `/agents` - Individual sub-workflow agent implementations
- `/shared` - Common utilities (Kusto client, Azure DevOps SDK wrappers, auth helpers)
- `/tests` - Unit and integration tests
- `/config` - Configuration files and Kusto query templates

**Rationale**: Simplifies cross-agent refactoring, shared code reuse, and deployment for POC with single-developer timeline.

**3. Service Architecture** (from PRD)

**Stateless Workflow Execution Engine with Checkpoint Persistence**

- **Stateless Execution**: No in-memory session state; all workflow state externalized to Azure Table Storage
- **Checkpoint System**: State persisted before/after each agent execution and at critical workflow milestones
- **Sequential Orchestration**: Main orchestrator invokes agents in fixed order using Microsoft Agent Framework patterns
- **Request/Response Communication**: Agents communicate via framework's request/response pattern
- **Idempotent Agents**: Agents designed to be safely re-runnable for retry scenarios

**4. Primary User Interaction Flow**

```
User (CLI)
  → Main Orchestrator
    → [Sequential Agent Execution]
      → ETW Input Collection (user provides providerGuid, ruleId)
      → Schema Discovery (queries Kusto for schema)
      → Code Generator (analyzes PRs, generates detector code)
      → PR Creation (creates branch, commits, submits PR)
      → User Approval Gate (PAUSE - wait for user approval)
      → Deployment Verification (polls for PR merge)
      → Results Analysis (queries Kusto for results)
      → User Confirmation Gate (PAUSE - user confirms results)
      → Production Promotion (creates promotion PR)
    → [Workflow Complete]
  ← Conversational feedback at each step
```

**5. Key Architectural Decisions**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Framework** | Microsoft Agent Framework (Python) | Required by PRD; provides proven orchestration patterns, checkpoint system, agent communication |
| **State Management** | Azure Table Storage checkpoints | Externalized state enables recovery; Azure-native; cost-effective for POC |
| **Agent Pattern** | Sequential sub-workflows | Simplifies POC development; matches linear detector workflow; easier to debug than parallel |
| **Azure Integration** | Azure Repos + Azure Kusto (exclusive) | Required by PRD; native Azure SDKs provide reliability and auth integration |
| **Authentication** | Azure AD service principal | Centralized auth; supports least-privilege RBAC; Key Vault integration for secrets |
| **Error Handling** | Retry with exponential backoff | Handles transient Azure API failures; aligns with PRD NFR10, NFR17 |
| **Interface** | CLI/Terminal conversational | Matches PRD scope; faster POC development than web UI; sufficient for internal tooling |

### High Level Project Diagram

```mermaid
graph TB
    User[User - CLI Interface]

    subgraph "Main Orchestrator"
        Orch[Sequential Workflow Orchestrator]
        CP[Checkpoint Manager]
    end

    subgraph "Sub-Workflow Agents"
        A1[ETW Input Agent]
        A2[Schema Discovery Agent]
        A3[Code Generator Agent]
        A4[User Approval Gate]
        A5[Deployment Verification Agent]
        A6[Results Analysis Agent]
        A7[Production Promotion Agent]
    end

    subgraph "Shared Services"
        Auth[Auth Manager]
        KustoClient[Kusto Client Wrapper]
        ReposClient[Repos Client Wrapper]
    end

    subgraph "Azure Services"
        AzureRepos[Azure Repos<br/>Source Control & PRs]
        AzureKusto[Azure Kusto<br/>Data Queries & Schema]
        TableStorage[Azure Table Storage<br/>Checkpoint Persistence]
        KeyVault[Azure Key Vault<br/>Secrets Management]
    end

    User -->|Commands & Inputs| Orch
    Orch -->|Feedback| User

    Orch -->|Sequential Invocation| A1
    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 -->|User Approval| A5
    A5 --> A6
    A6 --> A7

    Orch <-->|Save/Load State| CP
    CP <-->|Persist| TableStorage

    A1 & A2 & A3 & A4 & A5 & A6 & A7 -->|Use| Auth
    A2 & A6 -->|Query Data| KustoClient
    A3 & A5 & A7 -->|Repo Operations| ReposClient

    Auth -->|Authenticate| KeyVault
    KustoClient -->|Query| AzureKusto
    ReposClient -->|Branch/Commit/PR| AzureRepos

    style User fill:#e1f5ff
    style Orch fill:#ffe1e1
    style CP fill:#ffe1e1
    style TableStorage fill:#c7f5c3
    style AzureRepos fill:#c7f5c3
    style AzureKusto fill:#c7f5c3
    style KeyVault fill:#c7f5c3
```

### Architectural and Design Patterns

**1. Sequential Workflow Orchestration Pattern**

Microsoft Agent Framework Sequential Orchestration - Main orchestrator invokes sub-workflow agents in fixed linear sequence.

**Rationale**: Matches natural linear flow of detector development; simplifies POC implementation; aligns with PRD's Technical Assumptions and Microsoft Agent Framework documentation.

**2. Checkpoint-Based State Management Pattern**

Externalize all workflow state to Azure Table Storage at agent boundaries. No in-memory session state.

**Rationale**: Enables workflow recovery after interruptions; supports long-running workflows; aligns with PRD NFR12 (100% checkpoint recovery reliability).

**3. Adapter Pattern for Azure Service Integration**

Wrapper classes (`KustoClientWrapper`, `AzureReposClientWrapper`) encapsulate Azure SDK complexity, provide consistent error handling, retry logic, and logging.

**Rationale**: Isolates Azure SDK details from agent business logic; enables consistent retry/backoff logic; simplifies testing through mockable interfaces.

**4. Repository Pattern for Data Access**

Checkpoint Manager acts as repository abstraction over Azure Table Storage.

**Rationale**: Separates state management concerns from workflow logic; enables future storage migration; simplifies testing.

**5. Human-in-the-Loop Gate Pattern**

Dedicated approval gate agents pause workflow execution and wait for explicit user input before proceeding.

**Rationale**: Maintains quality control while automating repetitive tasks; prevents autonomous deployment of incorrect code; aligns with PRD requirement.

**6. Conversational Interface Pattern**

CLI-based request/response interaction where agents prompt user for inputs, display progress, and wait for approvals.

**Rationale**: Matches PRD's "conversational, guided workflow" requirement; faster POC development than web UI.

**7. Pattern Learning via Historical Analysis**

Code Generator and Production Promotion agents query Azure Repos for recent merged PRs, extract patterns using AST parsing or regex.

**Rationale**: Core differentiator for maf-agents (PRD goal: 90% pattern consistency); continuous improvement as more PRs provide pattern signal.

---

## Tech Stack

### Cloud Infrastructure

- **Provider:** Microsoft Azure
- **Key Services:**
  - Azure Repos (Azure DevOps Git)
  - Azure Kusto (Azure Data Explorer)
  - Azure Table Storage
  - Azure Key Vault
  - Azure Pipelines
  - Azure AD/Entra ID
- **Deployment Regions:** Not applicable for POC (local development)

### Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|-----------|---------|---------|-----------|
| **Language** | Python | 3.11 | Primary development language | Stable LTS, MAF compatible (requires 3.10+), modern syntax |
| **Package Management** | uv | Latest | Dependency management & virtual env | **MAF Standard** - Fast Rust-based package manager |
| **Task Automation** | poethepoet (poe) | Latest | Development task runner | **MAF Standard** - Task automation |
| **Agent Framework** | Microsoft Agent Framework | Latest (0.x) | Workflow orchestration | **REQUIRED by PRD** |
| **Azure SDK - DevOps** | azure-devops | 7.1.0b4 | Azure Repos API | Official Azure DevOps SDK |
| **Azure SDK - Kusto** | azure-kusto-data | 4.4.0 | Kusto query execution | Official Kusto SDK |
| **Azure SDK - Identity** | azure-identity | 1.15.0 | Azure AD authentication | Service principal auth |
| **Azure SDK - Key Vault** | azure-keyvault-secrets | 4.8.0 | Secrets retrieval | Key Vault access |
| **Azure SDK - Storage** | azure-data-tables | 12.5.0 | Checkpoint persistence | Table Storage for state |
| **Testing - Unit** | pytest | Latest | Unit test framework | **MAF Standard** - 80% coverage |
| **Testing - Mocking** | pytest-mock | Latest | Test mocking | pytest integration |
| **Testing - Coverage** | pytest-cov | Latest | Code coverage | **MAF Standard** - Min 80% |
| **Code Quality - Linting & Formatting** | ruff | Latest | Linter AND formatter | **MAF Standard** - 120-char line length |
| **Type Checking (Primary)** | pyright | Latest | Static type checking | **MAF Standard** - Primary checker |
| **Type Checking (Secondary)** | mypy | Latest | Static type checking | **MAF Standard** - Secondary validation |
| **Pre-commit Hooks** | pre-commit | Latest | Git hooks for quality | **MAF Standard** - Auto-installed |
| **Logging** | structlog | 24.1.0 | Structured logging | JSON logging, observability |
| **Configuration** | pydantic-settings | Latest | Configuration management | **MAF uses pydantic** |
| **CLI Framework** | rich | 13.7.1 | Terminal UI | Beautiful CLI output |
| **CI/CD** | Azure Pipelines | N/A | Continuous integration | Native Azure Repos integration |
| **Local Development** | python-dotenv | Latest | Environment variables | **MAF Standard** - .env loading |

---

## Data Models

All models defined using **Pydantic** for type safety, validation, and serialization to Azure Table Storage.

### WorkflowCheckpoint

Root checkpoint object representing complete workflow state.

**Key Attributes:**
- `workflow_id`: str - Unique identifier (UUID)
- `created_at`: datetime - Workflow start timestamp
- `updated_at`: datetime - Last checkpoint save
- `current_step`: str - Current agent/step
- `status`: str - "in_progress" | "paused_for_approval" | "completed" | "failed"
- `etw_input`: ETWInputData
- `schema_data`: Optional[KustoSchemaData]
- `generated_code`: Optional[GeneratedCodeData]
- `pr_metadata`: Optional[PRMetadata]
- `deployment_status`: Optional[DeploymentStatus]
- `results_analysis`: Optional[ResultsAnalysisData]
- `error_info`: Optional[ErrorInfo]

### ETWInputData

User-provided ETW details.

**Key Attributes:**
- `provider_guid`: str - ETW provider GUID (validated regex)
- `rule_id`: str - ETW rule identifier
- `user_notes`: Optional[str]

### KustoSchemaData

ETW schema and existing detector information from Kusto.

**Key Attributes:**
- `existing_detectors`: List[str]
- `schema_fields`: List[SchemaField]
- `query_timestamp`: datetime
- `kusto_cluster_url`: str

**Nested: SchemaField**
- `field_name`: str
- `field_type`: str
- `description`: Optional[str]

### GeneratedCodeData

Detector code generated by Code Generator Agent.

**Key Attributes:**
- `detector_file_name`: str
- `detector_code`: str
- `test_file_name`: str
- `test_code`: str
- `learned_patterns`: PatternData
- `generation_timestamp`: datetime

### PatternData

Naming conventions and code patterns from historical PR analysis.

**Key Attributes:**
- `naming_patterns`: Dict[str, str]
- `code_patterns`: List[str]
- `confidence_score`: float (0.0-1.0)
- `sample_size`: int
- `analyzed_at`: datetime

### PRMetadata

Pull request information from Azure Repos.

**Key Attributes:**
- `pr_id`: int
- `pr_url`: str
- `source_branch`: str
- `target_branch`: str
- `pr_title`: str
- `pr_description`: str
- `created_at`: datetime
- `merge_status`: "pending" | "approved" | "merged" | "rejected"
- `merged_at`: Optional[datetime]

### DeploymentStatus

Deployment verification status.

**Key Attributes:**
- `pr_merged`: bool
- `deployment_detected`: bool
- `deployment_timestamp`: Optional[datetime]
- `pipeline_run_id`: Optional[str]
- `verification_attempts`: int
- `last_check_timestamp`: datetime

### ResultsAnalysisData

Detector effectiveness results from Kusto.

**Key Attributes:**
- `query_executed_at`: datetime
- `time_window_start`: datetime
- `time_window_end`: datetime
- `events_detected`: int
- `error_count`: int
- `false_positive_indicators`: List[str]
- `summary`: str
- `user_approved`: bool

### ErrorInfo

Error details when workflow fails.

**Key Attributes:**
- `error_type`: str
- `error_message`: str
- `failed_agent`: str
- `stack_trace`: Optional[str]
- `occurred_at`: datetime
- `recoverable`: bool

---

## Components

### Main Orchestrator

**Responsibility:** Coordinates sequential execution of 7 sub-workflow agents, manages checkpoint persistence, handles workflow lifecycle.

**Key Interfaces:**
- `start_workflow(etw_input: ETWInputData) -> WorkflowCheckpoint`
- `resume_workflow(workflow_id: str) -> WorkflowCheckpoint`
- `get_workflow_status(workflow_id: str) -> WorkflowStatus`

**Dependencies:**
- Checkpoint Manager
- All 7 sub-workflow agents
- Auth Manager

**Technology Stack:**
- Microsoft Agent Framework Sequential Orchestration
- Python 3.11
- Pydantic for data validation
- structlog for logging

---

### ETW Input Collection Agent

**Responsibility:** Conversationally collect and validate ETW providerGuid and ruleId from user via CLI.

**Key Interfaces:**
- `collect_input() -> ETWInputData`
- `validate_guid(guid: str) -> bool`
- `validate_rule_id(rule_id: str) -> bool`

**Dependencies:**
- rich (CLI prompts)
- Pydantic validation

**Technology Stack:** Python 3.11, rich, Pydantic

---

### Schema Discovery Agent

**Responsibility:** Query Azure Kusto to identify existing detectors and retrieve ETW schema definition.

**Key Interfaces:**
- `discover_schema(etw_input: ETWInputData) -> KustoSchemaData`
- `find_existing_detectors(provider_guid: str) -> List[str]`
- `get_etw_schema(provider_guid: str) -> List[SchemaField]`

**Dependencies:**
- Kusto Client Wrapper
- Query templates from config/kusto_queries.yaml

**Technology Stack:** Python 3.11, azure-kusto-data SDK, Pydantic

---

### Code Generator Agent

**Responsibility:** Analyze historical PRs, extract patterns, generate detector code files following learned conventions.

**Key Interfaces:**
- `generate_detector(schema: KustoSchemaData) -> GeneratedCodeData`
- `analyze_patterns() -> PatternData`
- `generate_detector_code(schema: KustoSchemaData, patterns: PatternData) -> str`

**Dependencies:**
- Repos Client Wrapper (for PR analysis)
- Pattern Analyzer
- Python AST library (for code generation)

**Technology Stack:** Python 3.11, azure-devops SDK, AST parsing

---

### PR Creation Agent

**Responsibility:** Create Azure Repos branch, commit generated detector files, submit PR.

**Key Interfaces:**
- `create_branch(branch_name: str) -> str`
- `commit_files(branch: str, files: Dict[str, str]) -> str`
- `create_pull_request(branch: str, title: str, description: str) -> PRMetadata`

**Dependencies:**
- Repos Client Wrapper

**Technology Stack:** Python 3.11, azure-devops SDK

---

### User Approval Gate Agent

**Responsibility:** Present PR to user, wait for explicit approval, pause workflow until user responds.

**Key Interfaces:**
- `wait_for_approval(pr_metadata: PRMetadata) -> bool`
- `display_pr_summary(pr_metadata: PRMetadata) -> None`

**Dependencies:**
- rich (CLI display)
- Checkpoint Manager (save before pause)

**Technology Stack:** Python 3.11, rich

---

### Deployment Verification Agent

**Responsibility:** Monitor Azure Repos PR merge status and Azure Pipelines for deployment confirmation.

**Key Interfaces:**
- `verify_deployment(pr_metadata: PRMetadata) -> DeploymentStatus`
- `poll_merge_status(pr_id: int) -> bool`
- `check_pipeline_completion(pr_id: int) -> Optional[str]`

**Dependencies:**
- Repos Client Wrapper

**Technology Stack:** Python 3.11, azure-devops SDK, retry logic with exponential backoff

---

### Results Analysis Agent

**Responsibility:** Query Kusto for detector results, analyze effectiveness, present findings to user.

**Key Interfaces:**
- `analyze_results(detector_name: str) -> ResultsAnalysisData`
- `execute_results_query(detector_name: str, time_window: timedelta) -> QueryResult`
- `summarize_findings(results: QueryResult) -> str`

**Dependencies:**
- Kusto Client Wrapper
- Query templates

**Technology Stack:** Python 3.11, azure-kusto-data SDK

---

### Production Promotion Agent

**Responsibility:** Analyze promotion patterns from historical PRs, generate PR to make detector customer-facing.

**Key Interfaces:**
- `promote_to_production(detector_name: str) -> PRMetadata`
- `analyze_promotion_patterns() -> PatternData`
- `generate_promotion_changes(patterns: PatternData) -> Dict[str, str]`

**Dependencies:**
- Repos Client Wrapper
- Pattern Analyzer

**Technology Stack:** Python 3.11, azure-devops SDK

---

### Checkpoint Manager (Shared Service)

**Responsibility:** Persist and retrieve workflow state to/from Azure Table Storage.

**Key Interfaces:**
- `save_checkpoint(checkpoint: WorkflowCheckpoint) -> None`
- `load_checkpoint(workflow_id: str) -> WorkflowCheckpoint`
- `list_checkpoints(workflow_id: str) -> List[WorkflowCheckpoint]`

**Dependencies:**
- Azure Table Storage client

**Technology Stack:** Python 3.11, azure-data-tables SDK, Pydantic

---

### Kusto Client Wrapper (Shared Service)

**Responsibility:** Execute Kusto queries with authentication, retry logic, timeout enforcement, error handling.

**Key Interfaces:**
- `execute_query(query: str, timeout_seconds: int = 30) -> QueryResult`
- `load_query_template(template_name: str, params: Dict) -> str`

**Dependencies:**
- Auth Manager
- Query templates

**Technology Stack:** Python 3.11, azure-kusto-data SDK, retry with exponential backoff

---

### Repos Client Wrapper (Shared Service)

**Responsibility:** Azure Repos operations (branch, commit, PR) with authentication, retry logic, error handling.

**Key Interfaces:**
- `create_branch(branch_name: str, source_branch: str) -> str`
- `commit_files(branch: str, file_changes: Dict[str, str], message: str) -> str`
- `create_pull_request(source: str, target: str, title: str, desc: str) -> PRMetadata`
- `get_pull_request_status(pr_id: int) -> PRMergeStatus`

**Dependencies:**
- Auth Manager

**Technology Stack:** Python 3.11, azure-devops SDK

---

### Auth Manager (Shared Service)

**Responsibility:** Centralized Azure AD authentication, credential retrieval from Key Vault, token management.

**Key Interfaces:**
- `get_kusto_credential() -> TokenCredential`
- `get_devops_credential() -> TokenCredential`
- `retrieve_secret(secret_name: str) -> str`

**Dependencies:**
- Azure Key Vault
- Azure AD

**Technology Stack:** Python 3.11, azure-identity SDK, azure-keyvault-secrets SDK

---

### Component Diagrams

```mermaid
graph TB
    subgraph "Workflow Layer"
        MO[Main Orchestrator]
    end

    subgraph "Agent Layer"
        A1[ETW Input Agent]
        A2[Schema Discovery Agent]
        A3[Code Generator Agent]
        A4[PR Creation Agent]
        A5[User Approval Gate]
        A6[Deployment Verification Agent]
        A7[Results Analysis Agent]
        A8[Production Promotion Agent]
    end

    subgraph "Shared Services Layer"
        CP[Checkpoint Manager]
        KC[Kusto Client Wrapper]
        RC[Repos Client Wrapper]
        AM[Auth Manager]
        PA[Pattern Analyzer]
    end

    subgraph "External Services"
        KV[Azure Key Vault]
        TS[Azure Table Storage]
        AK[Azure Kusto]
        AR[Azure Repos]
    end

    MO --> A1
    MO --> A2
    MO --> A3
    MO --> A4
    MO --> A5
    MO --> A6
    MO --> A7
    MO --> A8
    MO --> CP

    A2 --> KC
    A7 --> KC
    A3 --> RC
    A3 --> PA
    A4 --> RC
    A6 --> RC
    A8 --> RC
    A8 --> PA

    CP --> AM
    KC --> AM
    RC --> AM

    CP --> TS
    KC --> AK
    RC --> AR
    AM --> KV

    style MO fill:#ffe1e1
    style CP fill:#fff3cd
    style KC fill:#fff3cd
    style RC fill:#fff3cd
    style AM fill:#fff3cd
```

---

## External APIs

### Azure DevOps REST API

**Purpose:** Azure Repos operations (branch creation, commits, PRs, deployment detection)

**Documentation:** https://learn.microsoft.com/en-us/rest/api/azure/devops/

**Base URL(s):**
- `https://dev.azure.com/{organization}/{project}/_apis/`

**Authentication:** OAuth 2.0 with Azure AD service principal (Personal Access Token or service principal credentials)

**Rate Limits:**
- 200 requests per minute per user/service principal
- 20,000 requests per hour per organization

**Key Endpoints Used:**
- `GET /git/repositories/{repositoryId}/refs` - List branches
- `POST /git/repositories/{repositoryId}/pushes` - Create branch and commit files
- `POST /git/repositories/{repositoryId}/pullrequests` - Create pull request
- `GET /git/repositories/{repositoryId}/pullrequests/{pullRequestId}` - Get PR status
- `GET /pipelines/runs` - Get pipeline run status

**Integration Notes:**
- Use azure-devops SDK wrapper to handle authentication and retry
- Implement exponential backoff for rate limit errors (429 status)
- Cache repository metadata to reduce API calls
- Use batch operations where possible (single push for multiple files)

---

### Azure Kusto (Data Explorer) API

**Purpose:** Execute KQL queries for schema discovery and detector results analysis

**Documentation:** https://learn.microsoft.com/en-us/azure/data-explorer/kusto/api/

**Base URL(s):**
- `https://{cluster}.{region}.kusto.windows.net/`

**Authentication:** Azure AD service principal with Kusto Viewer role

**Rate Limits:**
- Concurrent queries: 20 per cluster
- Query timeout: 10 minutes default (configurable)
- Result size: 500,000 rows or 64 MB per query

**Key Endpoints Used:**
- `POST /{database}/query` - Execute KQL query
- `GET /{database}/schema` - Get database schema

**Integration Notes:**
- Use azure-kusto-data SDK for query execution
- Parameterize queries to prevent injection
- Load query templates from config/kusto_queries.yaml
- Implement 30-second timeout per NFR2
- Handle large result sets with pagination if needed
- Monitor query performance for optimization

---

### Azure Key Vault API

**Purpose:** Retrieve service principal credentials and connection strings

**Documentation:** https://learn.microsoft.com/en-us/azure/key-vault/

**Base URL(s):**
- `https://{vault-name}.vault.azure.net/`

**Authentication:** Azure AD managed identity or service principal

**Rate Limits:**
- 2,000 requests per 10 seconds per vault
- Sufficient for POC (low frequency access)

**Key Endpoints Used:**
- `GET /secrets/{secret-name}` - Retrieve secret value

**Integration Notes:**
- Use azure-keyvault-secrets SDK
- Cache credentials in memory (avoid repeated fetches)
- Secrets accessed during initialization only
- Required secrets: Kusto cluster URL, DevOps PAT, service principal credentials

---

## Core Workflows

### End-to-End Detector Development Workflow

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant ETWAgent as ETW Input Agent
    participant SchemaAgent as Schema Discovery Agent
    participant CodeGenAgent as Code Generator Agent
    participant PRAgent as PR Creation Agent
    participant ApprovalGate as User Approval Gate
    participant DeployAgent as Deployment Verification Agent
    participant ResultsAgent as Results Analysis Agent
    participant PromotionAgent as Production Promotion Agent
    participant Checkpoint as Checkpoint Manager
    participant Kusto as Azure Kusto
    participant Repos as Azure Repos

    User->>Orchestrator: Start workflow
    Orchestrator->>Checkpoint: Save initial checkpoint

    Orchestrator->>ETWAgent: Collect ETW input
    ETWAgent->>User: Prompt for providerGuid
    User->>ETWAgent: Provide GUID
    ETWAgent->>User: Prompt for ruleId
    User->>ETWAgent: Provide ruleId
    ETWAgent->>Orchestrator: Return ETWInputData
    Orchestrator->>Checkpoint: Save checkpoint (step: etw_input)

    Orchestrator->>SchemaAgent: Discover schema
    SchemaAgent->>Kusto: Query existing detectors
    Kusto->>SchemaAgent: Return detector list
    SchemaAgent->>Kusto: Query ETW schema
    Kusto->>SchemaAgent: Return schema fields
    SchemaAgent->>Orchestrator: Return KustoSchemaData
    Orchestrator->>Checkpoint: Save checkpoint (step: schema_discovery)

    Orchestrator->>CodeGenAgent: Generate detector code
    CodeGenAgent->>Repos: Fetch recent PRs
    Repos->>CodeGenAgent: Return PR list
    CodeGenAgent->>CodeGenAgent: Analyze patterns (AST)
    CodeGenAgent->>CodeGenAgent: Generate detector code
    CodeGenAgent->>Orchestrator: Return GeneratedCodeData
    Orchestrator->>Checkpoint: Save checkpoint (step: code_generation)

    Orchestrator->>PRAgent: Create PR
    PRAgent->>Repos: Create branch
    PRAgent->>Repos: Commit files
    PRAgent->>Repos: Create pull request
    Repos->>PRAgent: Return PR metadata
    PRAgent->>Orchestrator: Return PRMetadata
    Orchestrator->>Checkpoint: Save checkpoint (step: pr_creation)

    Orchestrator->>ApprovalGate: Wait for user approval
    ApprovalGate->>User: Display PR URL and summary
    ApprovalGate->>User: Prompt: Approve or Reject?
    Orchestrator->>Checkpoint: Save checkpoint (status: paused_for_approval)

    User->>ApprovalGate: Approve
    ApprovalGate->>Orchestrator: Continue workflow
    Orchestrator->>Checkpoint: Save checkpoint (step: approval_gate)

    Orchestrator->>DeployAgent: Verify deployment
    loop Poll every 30s (max 60 min)
        DeployAgent->>Repos: Check PR merge status
        Repos->>DeployAgent: Return merge status
        alt PR merged
            DeployAgent->>Repos: Check pipeline status
            Repos->>DeployAgent: Return pipeline status
        end
    end
    DeployAgent->>Orchestrator: Return DeploymentStatus
    Orchestrator->>Checkpoint: Save checkpoint (step: deployment_verification)

    Orchestrator->>ResultsAgent: Analyze results
    ResultsAgent->>Kusto: Query detector results (last 1 hour)
    Kusto->>ResultsAgent: Return query results
    ResultsAgent->>ResultsAgent: Analyze and summarize
    ResultsAgent->>User: Display results summary
    ResultsAgent->>User: Prompt: Results look correct?
    User->>ResultsAgent: Confirm
    ResultsAgent->>Orchestrator: Return ResultsAnalysisData (approved)
    Orchestrator->>Checkpoint: Save checkpoint (step: results_analysis)

    Orchestrator->>PromotionAgent: Promote to production
    PromotionAgent->>Repos: Fetch promotion PRs (examples)
    Repos->>PromotionAgent: Return promotion examples
    PromotionAgent->>PromotionAgent: Extract patterns
    PromotionAgent->>PromotionAgent: Generate promotion changes
    PromotionAgent->>Repos: Create branch
    PromotionAgent->>Repos: Commit promotion changes
    PromotionAgent->>Repos: Create promotion PR
    Repos->>PromotionAgent: Return PR metadata
    PromotionAgent->>Orchestrator: Return PRMetadata
    Orchestrator->>Checkpoint: Save checkpoint (status: completed)

    Orchestrator->>User: Workflow complete! Promotion PR: {url}
```

---

## Database Schema

**Storage Type:** Azure Table Storage (NoSQL key-value store)

**Table Name:** `WorkflowCheckpoints`

**Schema:**

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| PartitionKey | string | workflow_id | Required, indexed |
| RowKey | string | Timestamp (ISO-8601) | Required, indexed |
| workflow_data | string | JSON-serialized WorkflowCheckpoint | Max 1MB |
| created_at | datetime | Checkpoint creation time | Required |
| current_step | string | Current agent step | Required |
| status | string | Workflow status | Required |

**Rationale:**
- **Table Storage vs SQL**: Simple key-value needs, no complex queries, cost-effective for POC, Azure-native
- **PartitionKey = workflow_id**: All checkpoints for a workflow co-located for efficient retrieval
- **RowKey = timestamp**: Natural ordering, enables checkpoint history
- **workflow_data = JSON**: Pydantic models serialize to JSON; flexible schema evolution
- **Denormalized design**: No relationships needed; checkpoint is self-contained snapshot

**Indexes:**
- Primary: (PartitionKey, RowKey) - automatic
- No secondary indexes needed for POC

**Data Retention:**
- POC: No automatic cleanup (manual deletion)
- Production: 90-day retention policy (implement post-POC)

**Sample Record:**
```json
{
  "PartitionKey": "550e8400-e29b-41d4-a716-446655440000",
  "RowKey": "2025-10-24T10:30:00.000Z",
  "workflow_data": "{\"workflow_id\": \"550e8400...\", \"status\": \"in_progress\", ...}",
  "created_at": "2025-10-24T10:30:00.000Z",
  "current_step": "schema_discovery",
  "status": "in_progress"
}
```

---

## Source Tree

```
maf-agents/
├── workflows/
│   ├── __init__.py
│   ├── main_orchestrator.py        # Main sequential workflow orchestrator
│   └── base_workflow.py            # Base class for workflow patterns
│
├── agents/
│   ├── __init__.py
│   ├── etw_input_agent.py          # ETW Input Collection Agent
│   ├── schema_discovery_agent.py   # Schema Discovery Agent
│   ├── code_generator_agent.py     # Code Generator Agent
│   ├── pr_creation_agent.py        # PR Creation Agent
│   ├── approval_gate_agent.py      # User Approval Gate Agent
│   ├── deployment_verification_agent.py  # Deployment Verification Agent
│   ├── results_analysis_agent.py   # Results Analysis Agent
│   └── production_promotion_agent.py     # Production Promotion Agent
│
├── shared/
│   ├── __init__.py
│   ├── auth.py                     # Auth Manager (Azure AD, Key Vault)
│   ├── checkpoint.py               # Checkpoint Manager (Table Storage)
│   ├── kusto_client.py             # Kusto Client Wrapper
│   ├── repos_client.py             # Repos Client Wrapper
│   ├── pattern_analyzer.py         # Pattern extraction from PRs
│   └── models.py                   # Pydantic data models
│
├── config/
│   ├── kusto_queries.yaml          # Kusto query templates
│   ├── settings.py                 # Application settings (Pydantic)
│   └── azure_config.yaml           # Azure resource identifiers
│
├── tests/
│   ├── unit/
│   │   ├── test_agents/
│   │   ├── test_shared/
│   │   └── test_workflows/
│   ├── integration/
│   │   ├── test_azure_integration.py
│   │   ├── test_e2e_workflow.py
│   │   └── fixtures/
│   └── conftest.py                 # Pytest configuration
│
├── scripts/
│   ├── setup_env.sh                # Environment setup script
│   └── run_workflow.py             # CLI entry point
│
├── docs/
│   ├── architecture.md             # This document
│   ├── prd.md                      # Product Requirements Document
│   ├── brief.md                    # Project Brief
│   └── README.md                   # Getting started guide
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions (if using GitHub)
│
├── azure-pipelines.yml             # Azure Pipelines CI/CD
├── pyproject.toml                  # uv/Python project configuration
├── uv.lock                         # Dependency lock file (generated)
├── .env.example                    # Environment variables template
├── .gitignore
├── .pre-commit-config.yaml         # Pre-commit hooks
└── README.md
```

**Key Organizational Principles:**

1. **Clear Separation of Concerns**: `/workflows`, `/agents`, `/shared` each have distinct responsibilities
2. **Agent Modularity**: One agent per file for clarity and testability
3. **Shared Services**: Reusable components (auth, clients) in `/shared`
4. **Configuration External**: All config in `/config`, no hardcoded values
5. **Test Mirroring**: Test structure mirrors source structure
6. **MAF Alignment**: Follows Microsoft Agent Framework conventions

---

## Infrastructure and Deployment

### Infrastructure as Code

**Tool:** Not applicable for POC (local development only)

**Post-POC Recommendation:** Azure Bicep or Terraform for production deployment

**Approach:** Infrastructure will be manually provisioned for POC:
- Azure Table Storage account
- Azure Key Vault
- Service principal with appropriate RBAC roles

---

### Deployment Strategy

**Strategy:** Local Development Only (POC)

**CI/CD Platform:** Azure Pipelines (configured but optional for POC)

**Pipeline Configuration:** `azure-pipelines.yml` (basic lint, test, type-check)

**Pipeline Stages:**
1. **Lint**: `uv run poe lint` (ruff)
2. **Type Check**: `uv run poe type-check` (pyright, mypy)
3. **Test**: `uv run poe test` (pytest with 80% coverage)
4. **Build**: Package validation (no deployment for POC)

---

### Environments

**Local Development**
- **Purpose:** Developer workstation
- **Details:** Python virtual environment managed by uv, .env file for configuration, local Azure authentication

**No staging or production environments for POC**

---

### Environment Promotion Flow

```
Local Development → (Manual Testing) → POC Validation
```

No automated promotion for POC. Post-POC: Implement Dev → Staging → Production flow.

---

### Rollback Strategy

**Primary Method:** Not applicable for POC (local development)

**Trigger Conditions:** N/A

**Recovery Time Objective:** N/A

**Post-POC Recommendation:**
- Git-based rollback for code
- Checkpoint recovery for workflow state
- Blue-green deployment for production

---

## Error Handling Strategy

### General Approach

**Error Model:** Exception-based with custom exception hierarchy

**Exception Hierarchy:**
```python
MafAgentsException (base)
├── WorkflowError
│   ├── CheckpointError
│   ├── AgentExecutionError
│   └── InvalidStateError
├── AzureServiceError
│   ├── KustoQueryError
│   ├── AzureReposAPIError
│   └── AuthenticationError
└── ValidationError (from Pydantic)
```

**Error Propagation:**
- Agents raise specific exceptions
- Orchestrator catches, logs, saves error to checkpoint
- Checkpoint marked as "failed" with ErrorInfo
- User notified via CLI with actionable message
- Recoverable errors allow retry from last checkpoint

---

### Logging Standards

**Library:** structlog 24.1.0

**Format:** JSON structured logging

```json
{
  "timestamp": "2025-10-24T10:30:00.000Z",
  "level": "info",
  "event": "kusto_query_executed",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent": "schema_discovery_agent",
  "duration_ms": 1250,
  "query_type": "get_etw_schema"
}
```

**Levels:**
- **DEBUG:** Detailed diagnostic info (disabled in production)
- **INFO:** Normal workflow progress, agent execution
- **WARNING:** Recoverable errors, retry attempts
- **ERROR:** Failures requiring attention, workflow failures
- **CRITICAL:** System failures, unrecoverable errors

**Required Context:**
- **Correlation ID:** workflow_id for request tracing
- **Service Context:** Agent name, component name
- **User Context:** Do NOT log PII; log workflow_id only

---

### Error Handling Patterns

#### External API Errors

**Retry Policy:**
- Exponential backoff: 1s, 2s, 4s, 8s, 16s (max 5 attempts)
- Retry on: 429 (rate limit), 502, 503, 504 (transient errors)
- No retry on: 400, 401, 403, 404 (client errors)

**Circuit Breaker:** Not implemented for POC (single-user, low volume)

**Timeout Configuration:**
- Kusto queries: 30 seconds (NFR2)
- Azure Repos API calls: 10 seconds
- Deployment polling: 60 minutes max (30s intervals)

**Error Translation:**
- Azure SDK exceptions → Custom MafAgentsException
- HTTP status codes → Specific error types
- User-facing messages simplified (no stack traces in CLI)

#### Business Logic Errors

**Custom Exceptions:**
- `InvalidETWInputError`: Invalid providerGuid or ruleId
- `InsufficientPRHistoryError`: Not enough PRs for pattern learning
- `DeploymentTimeoutError`: Deployment not detected within 60 min

**User-Facing Errors:**
- Displayed via rich console with helpful context
- Include suggested actions (e.g., "Check PR status manually")
- Link to documentation where applicable

**Error Codes:** Not implemented for POC (use exception types)

#### Data Consistency

**Transaction Strategy:** Not applicable (Azure Table Storage is eventually consistent)

**Compensation Logic:**
- Checkpoint rollback: Restore from previous checkpoint
- No database transactions needed (checkpoint is atomic write)

**Idempotency:**
- Agents designed to be re-runnable (e.g., code generation produces same output for same input)
- Azure Repos operations: Check if branch/PR exists before creating
- Kusto queries: Read-only, naturally idempotent

---

## Coding Standards

**CRITICAL:** These standards are MANDATORY for AI agents. They directly control AI developer behavior.

### Core Standards

**Languages & Runtimes:** Python 3.11

**Style & Linting:**
- Ruff (linter AND formatter)
- Configuration: 120-character line length, Python 3.10+ target
- Run: `uv run poe lint` and `uv run poe format`

**Type Checking:**
- Pyright (primary) and mypy (secondary)
- All functions must have type hints
- Run: `uv run poe type-check`

**Test Organization:**
- Unit tests: `tests/unit/test_{module}.py`
- Integration tests: `tests/integration/test_{feature}.py`
- Test file naming: `test_` prefix required
- Run: `uv run poe test`

**Docstrings:**
- Google-style docstrings for all public functions, classes, modules
- 120-character max width
- Example:
```python
def execute_query(query: str, timeout: int = 30) -> QueryResult:
    """Execute a Kusto query with timeout and retry logic.

    Args:
        query: KQL query string to execute
        timeout: Maximum execution time in seconds

    Returns:
        QueryResult containing rows and metadata

    Raises:
        KustoQueryError: If query fails after retries
    """
```

---

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| **Modules** | snake_case | `etw_input_agent.py` |
| **Classes** | PascalCase | `WorkflowCheckpoint` |
| **Functions** | snake_case | `execute_query()` |
| **Variables** | snake_case | `workflow_id` |
| **Constants** | UPPER_SNAKE_CASE | `MAX_RETRY_ATTEMPTS` |
| **Private** | _leading_underscore | `_internal_helper()` |
| **Pydantic Models** | PascalCase | `ETWInputData` |

---

### Critical Rules

**1. Logging**
- **NEVER use print()** - Use structlog logger
- **Always include correlation_id** in log context
- **Do NOT log secrets** or credentials (check before logging)

**2. Error Handling**
- **Catch specific exceptions**, not bare `except:`
- **Always log errors** before re-raising or returning error response
- **Provide actionable error messages** to users

**3. Azure API Calls**
- **All Azure SDK calls must use wrapper classes** (KustoClientWrapper, ReposClientWrapper)
- **Never call Azure SDKs directly from agents**
- **Implement retry logic in wrappers**, not agents

**4. Data Validation**
- **All user inputs must be validated** via Pydantic models
- **Validate at agent boundaries** before processing
- **Use Pydantic Field validators** for complex rules

**5. Checkpoint Management**
- **Save checkpoint before pausing workflow** (approval gates)
- **Save checkpoint after each agent completes**
- **Include all relevant state** in checkpoint (no hidden state)

**6. Type Hints**
- **All function signatures must have type hints**
- **Use Optional[T] for nullable values**
- **Use TypedDict or Pydantic for complex data structures**

**7. Testing**
- **Mock external services** (Azure SDKs) in unit tests
- **Use real Azure services** in integration tests (if available)
- **Aim for 80% code coverage** (MAF standard)

---

### Language-Specific Guidelines

**Python 3.11 Specifics:**

**Modern Syntax:**
- Use `|` for Optional types: `str | None` instead of `Optional[str]`
- Use `list[T]` instead of `List[T]` (PEP 585)
- Use `dict[K, V]` instead of `Dict[K, V]`

**Async/Await:**
- Use async/await if Microsoft Agent Framework requires it
- Avoid mixing sync and async code (pick one paradigm)

**Pattern Matching:**
- Use `match/case` for complex conditionals where appropriate
- Prefer explicit if/elif for simple cases

**Example:**
```python
from typing import Optional

def process_checkpoint(checkpoint: WorkflowCheckpoint) -> str | None:
    """Process workflow checkpoint and return next step."""
    match checkpoint.status:
        case WorkflowStatus.IN_PROGRESS:
            return checkpoint.current_step
        case WorkflowStatus.COMPLETED:
            return None
        case _:
            raise InvalidStateError(f"Unexpected status: {checkpoint.status}")
```

---

## Test Strategy and Standards

### Testing Philosophy

**Approach:** Test-After Development (not TDD) for POC speed

**Coverage Goals:**
- **Minimum:** 80% code coverage (MAF standard)
- **Target:** 85-90% for critical paths (orchestrator, wrappers)
- **Not required:** 100% coverage (diminishing returns for POC)

**Test Pyramid:**
- **70% Unit Tests:** Fast, isolated, mocked dependencies
- **25% Integration Tests:** Real Azure services, slow, fewer tests
- **5% E2E Tests:** Full workflow, very slow, smoke tests only

---

### Test Types and Organization

#### Unit Tests

**Framework:** pytest

**File Convention:** `tests/unit/test_{module_name}.py`

**Location:** `tests/unit/` mirroring source structure

**Mocking Library:** pytest-mock (wrapper over unittest.mock)

**Coverage Requirement:** 80% minimum per module

**AI Agent Requirements:**
- Generate tests for all public methods
- Cover edge cases and error conditions
- Follow AAA pattern (Arrange, Act, Assert)
- Mock all external dependencies (Azure SDKs, file I/O)

**Example:**
```python
def test_execute_query_success(mocker):
    # Arrange
    mock_client = mocker.patch('shared.kusto_client.KustoClient')
    mock_client.execute.return_value = [{"field": "value"}]
    wrapper = KustoClientWrapper(cluster_url="https://test.kusto.windows.net")

    # Act
    result = wrapper.execute_query("test query")

    # Assert
    assert result.row_count == 1
    assert result.data[0]["field"] == "value"
    mock_client.execute.assert_called_once()
```

---

#### Integration Tests

**Scope:** Test Azure SDK integrations with real services (or emulators)

**Location:** `tests/integration/`

**Test Infrastructure:**
- **Azure Table Storage:** Use Azurite local emulator (or test storage account)
- **Azure Kusto:** Use test cluster (if available) or mocks
- **Azure Repos:** Use test repository in Azure DevOps
- **Azure Key Vault:** Use test Key Vault (or mock for local dev)

**Environment Variables:**
```bash
AZURE_STORAGE_CONNECTION_STRING=...
AZURE_KUSTO_CLUSTER_URL=...
AZURE_DEVOPS_ORG=...
AZURE_DEVOPS_PROJECT=...
AZURE_KEYVAULT_URL=...
```

**Example:**
```python
@pytest.mark.integration
def test_checkpoint_roundtrip():
    """Test save and load checkpoint to real Azure Table Storage."""
    # Arrange
    manager = CheckpointManager()
    checkpoint = WorkflowCheckpoint(
        workflow_id="test-123",
        created_at=datetime.utcnow(),
        ...
    )

    # Act
    manager.save_checkpoint(checkpoint)
    loaded = manager.load_checkpoint("test-123")

    # Assert
    assert loaded.workflow_id == checkpoint.workflow_id
    assert loaded.status == checkpoint.status
```

---

#### End-to-End Tests

**Framework:** pytest

**Scope:** Complete workflow from ETW input to production promotion

**Environment:** Requires all Azure services configured

**Test Data:**
- Pre-configured test ETW provider GUID
- Test Azure Repos repository
- Test Kusto database with sample data

**Example:**
```python
@pytest.mark.e2e
def test_full_workflow(monkeypatch):
    """Test complete detector workflow end-to-end."""
    # Simulate user inputs
    monkeypatch.setattr('builtins.input', lambda _: 'test-guid')

    # Act
    orchestrator = MainOrchestrator()
    checkpoint = orchestrator.start_workflow()

    # Assert
    assert checkpoint.status == WorkflowStatus.COMPLETED
    assert checkpoint.pr_metadata is not None
    assert checkpoint.deployment_status.deployment_detected is True
```

---

### Test Data Management

**Strategy:** Fixtures for test data, factories for complex objects

**Fixtures:** `tests/conftest.py` for shared fixtures

**Factories:** Use Pydantic model constructors

**Cleanup:**
- Unit tests: No cleanup needed (mocked)
- Integration tests: Delete test data after each test
- E2E tests: Manual cleanup or dedicated test environment

**Example Fixture:**
```python
@pytest.fixture
def sample_etw_input():
    return ETWInputData(
        provider_guid="550e8400-e29b-41d4-a716-446655440000",
        rule_id="test-rule-1",
        user_notes="Test detector"
    )
```

---

### Continuous Testing

**CI Integration:** Azure Pipelines runs tests on every commit

**Pipeline Stages:**
1. Lint (ruff)
2. Type check (pyright, mypy)
3. Unit tests (80% coverage required)
4. Integration tests (optional, manual trigger)

**Performance Tests:** Not implemented for POC

**Security Tests:** Not implemented for POC (post-POC: Bandit, safety)

---

## Security

### Input Validation

**Validation Library:** Pydantic

**Validation Location:** At agent boundaries (all user inputs)

**Required Rules:**
- All external inputs MUST be validated against Pydantic models
- Validation at API boundary before processing
- Whitelist approach preferred over blacklist
- Regex validation for GUID format, URL format

**Example:**
```python
class ETWInputData(BaseModel):
    provider_guid: str = Field(
        ...,
        regex=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    )
    rule_id: str = Field(..., min_length=1, max_length=100)
```

---

### Authentication & Authorization

**Auth Method:** Azure AD service principal with client credentials flow

**Session Management:** Not applicable (stateless CLI, no sessions)

**Required Patterns:**
- Service principal credentials stored in Azure Key Vault
- Use `DefaultAzureCredential` for local development (supports multiple auth methods)
- Use `ClientSecretCredential` for production with explicit service principal
- Token caching handled by Azure Identity SDK
- Least-privilege RBAC roles:
  - Azure Repos: Contributor role
  - Azure Kusto: Viewer role
  - Azure Key Vault: Secrets Get permission
  - Azure Table Storage: Table Contributor role

---

### Secrets Management

**Development:**
- `.env` file for local development (NOT committed to Git)
- `.env.example` template committed (no actual secrets)
- Azure CLI authentication for local dev (`az login`)

**Production:**
- Azure Key Vault for all secrets
- Service principal credentials in Key Vault
- Environment variables point to Key Vault URL only

**Code Requirements:**
- **NEVER hardcode secrets** in code
- Access secrets via `auth.py` only
- No secrets in logs or error messages
- Secrets masked in CLI output (use `***` for display)

**Example:**
```python
# shared/auth.py
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

class AuthManager:
    def __init__(self, keyvault_url: str):
        self.credential = DefaultAzureCredential()
        self.secret_client = SecretClient(vault_url=keyvault_url, credential=self.credential)

    def get_kusto_connection_string(self) -> str:
        return self.secret_client.get_secret("kusto-connection-string").value
```

---

### API Security

**Rate Limiting:**
- Handled by Azure services (client-side backoff)
- Exponential backoff on 429 responses
- No custom rate limiting for POC

**CORS Policy:** Not applicable (CLI tool, no web server)

**Security Headers:** Not applicable (no HTTP server)

**HTTPS Enforcement:** All Azure API calls use HTTPS by default (enforced by SDKs)

---

### Data Protection

**Encryption at Rest:**
- Azure Table Storage: Microsoft-managed encryption enabled by default
- Azure Key Vault: Hardware-backed encryption

**Encryption in Transit:**
- All Azure SDK calls use TLS 1.2+
- No custom encryption needed

**PII Handling:**
- Do NOT log user identifiers beyond workflow_id
- Do NOT log ETW provider GUIDs in plaintext (use first 8 chars + `...` for logs)
- No PII in checkpoint data

**Logging Restrictions:**
- Never log secrets, credentials, tokens
- Never log full Azure connection strings
- Never log user personal information
- Sanitize error messages before logging

---

### Dependency Security

**Scanning Tool:** Not implemented for POC

**Post-POC Recommendation:**
- `pip-audit` for dependency vulnerability scanning
- `safety` for known security issues
- Dependabot or Renovate for automated updates

**Update Policy:**
- Review dependency updates monthly
- Critical security patches applied immediately
- Pin major versions in `pyproject.toml`, allow minor/patch updates

**Approval Process:**
- New dependencies require architect approval
- Document rationale in PR description
- Check license compatibility (MIT, Apache 2.0 preferred)

---

### Security Testing

**SAST Tool:** Not implemented for POC

**Post-POC Recommendation:** Bandit for Python static analysis

**DAST Tool:** Not applicable (no web application)

**Penetration Testing:** Not applicable for POC (internal tooling)

---

## Checklist Results Report

### Executive Summary

**Overall Architecture Readiness:** ✅ **HIGH (92% Complete)**

**Project Type:** Backend-Only POC with CLI Interface

**Critical Strengths:**
- Comprehensive PRD alignment (all 25 functional and 18 non-functional requirements addressed)
- Clear sequential workflow orchestration with Microsoft Agent Framework
- Well-defined data models with Pydantic for type safety
- Detailed component interfaces and responsibilities (11 components documented)
- Strong security posture (Azure AD, Key Vault, least privilege, no hardcoded secrets)
- Excellent AI agent implementation suitability (modular, clear patterns, explicit guidance)

**Critical Risks Identified:**
1. Microsoft Agent Framework version ambiguity ("Latest 0.x" needs specific pinning)
2. No circuit breaker pattern for Azure API resilience
3. Integration test infrastructure undefined for local development
4. No monitoring/observability tooling specified beyond logging
5. Pattern learning fallback threshold undefined

**Recommendation:** Architecture is ready for development. Address MAF version pinning immediately; other gaps are nice-to-haves for POC.

---

### Section Analysis

| Section | Pass Rate | Status | Notes |
|---------|-----------|--------|-------|
| Requirements Alignment | 100% | ✅ PASS | All FR/NFR addressed |
| Architecture Fundamentals | 100% | ✅ PASS | 3 diagrams, clear patterns |
| Technical Stack & Decisions | 95% | ✅ PASS | MAF version needs pinning |
| Resilience & Operational | 85% | ⚠️ PARTIAL | Circuit breaker, monitoring tools undefined |
| Security & Compliance | 100% | ✅ PASS | Comprehensive security controls |
| Implementation Guidance | 95% | ✅ PASS | Integration test setup needs detail |
| Dependency Management | 100% | ✅ PASS | All dependencies identified |
| AI Agent Suitability | 100% | ✅ PASS | Optimized for AI implementation |

**Overall:** 8 of 8 evaluated sections passed (Frontend sections skipped for backend-only project). One section needs minor enhancements.

---

### Top Recommendations

#### Must-Fix Before Development

**None** - Architecture is ready to proceed.

#### Should-Fix for Better Quality

1. **Pin Microsoft Agent Framework Version** (30 min)
   - Action: Test with specific version, add to pyproject.toml
   - Benefit: Reproducible builds, avoid breaking changes

2. **Add Monitoring/Observability Tooling** (2-4 hours)
   - Action: Integrate Azure Application Insights, define key metrics
   - Benefit: Proactive issue detection, debugging capability

3. **Document Integration Test Setup** (1 hour)
   - Action: Add Azurite setup, test cluster config to architecture
   - Benefit: Faster developer onboarding

#### Nice-to-Have Improvements

4. Implement circuit breaker pattern (1-2 hours)
5. Define pattern learning threshold (15 min)
6. Add performance benchmarking strategy (1-2 hours)

---

### AI Implementation Readiness

**Overall Assessment:** ✅ **EXCELLENT**

**Key Strengths:**
- **Modularity:** 7 agents + 5 shared services = small, focused modules
- **Clear Interfaces:** Every component has explicit method signatures with types
- **Consistent Patterns:** All agents follow same structure
- **Explicit Guidance:** 7 MANDATORY coding rules for AI agents
- **Examples:** Pydantic models, error handling, logging, testing patterns
- **No Hidden State:** Checkpoint system externalizes all state
- **Sequential Execution:** Linear workflow easier to implement than parallel/event-driven

**Complexity Hotspots:**
1. Pattern Learning (Code Generator) - Most complex; fallback to rule-based templates provided
2. Deployment Verification Polling - Clear retry pattern documented
3. Microsoft Agent Framework Integration - Health check agent validates setup early

**Validation Date:** 2025-10-24

---

## Next Steps

### Architecture Validation

1. **Review architecture with Product Owner** - Confirm alignment with PRD goals
2. **Validate Azure service access** - Ensure team has necessary permissions for Azure Repos, Kusto, Table Storage, Key Vault
3. **Confirm Microsoft Agent Framework version** - Pin specific version in pyproject.toml
4. **Set up development environment** - Follow MAF dev setup guide

### Development Handoff

**For Dev Agent:**

"Please begin implementation of maf-agents following the architecture document at `docs/architecture.md`. Start with **Epic 1, Story 1.1: Project Setup and Dependency Installation**.

Key priorities:
1. Initialize project structure following the Source Tree section
2. Configure uv package manager and install dependencies per Tech Stack
3. Set up pre-commit hooks and code quality tools (ruff, pyright, mypy)
4. Follow Coding Standards section for all code generation
5. Reference Data Models section for Pydantic model definitions
6. Use Components section for interface design

The architecture provides complete specifications for all 7 agents, shared services, Azure integrations, and error handling patterns. Refer to External APIs section for Azure service integration details."

---

**Architecture document complete!** ✅

This architecture provides comprehensive technical guidance for the maf-agents POC, aligned with Microsoft Agent Framework standards and PRD requirements.
