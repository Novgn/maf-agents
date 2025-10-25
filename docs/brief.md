# Project Brief: maf-agents

## Executive Summary

**maf-agents** is a proof-of-concept conversational multi-agentic AI system built on Microsoft Agent Framework (Python) that automates the end-to-end lifecycle of Azure detector development. The system accepts ETW (Event Tracing for Windows) details, queries Azure Kusto clusters to validate schemas, generates detector code by learning from historical PR patterns, manages the PR approval process, verifies deployment, analyzes detector results, and promotes detectors to customer-facing status—all through an intelligent, conversational workflow with human-in-the-loop approval gates.

**Target Market**: Internal engineering teams working with Azure detector development and ETW-based monitoring systems.

**Key Value Proposition**: Reduces detector development cycle time from hours/days to minutes by automating repetitive tasks while maintaining quality through pattern-learning and human oversight.

---

## Problem Statement

### Current State and Pain Points

Developing Azure detectors for ETW-based monitoring is a manual, time-consuming, and error-prone process that involves:

- **Manual schema validation**: Engineers must query Kusto clusters to understand ETW schemas and identify existing detectors
- **Inconsistent code patterns**: Without automated pattern extraction, detector implementations vary in quality and style
- **Context switching overhead**: Developers juggle multiple tools (Kusto explorer, Azure DevOps, code editors) to complete a single detector
- **Delayed feedback loops**: Time between detector creation, deployment verification, and results analysis creates bottlenecks
- **Repetitive promotion work**: Converting internal detectors to customer-facing requires manual pattern matching from previous examples

### Impact of the Problem

- **Productivity loss**: 4-8 hours per detector for experienced engineers, longer for newcomers
- **Quality inconsistency**: Manual processes lead to bugs, missed conventions, and technical debt
- **Knowledge bottlenecks**: Detector development expertise concentrated in few team members
- **Slow iteration cycles**: Delays in getting detectors to production impact monitoring coverage

### Why Existing Solutions Fall Short

- **Generic CI/CD pipelines**: Don't understand detector-specific patterns or ETW schemas
- **Documentation and templates**: Static resources become outdated and don't learn from repo history
- **Code generation tools**: Lack integration with Kusto validation and deployment verification
- **Manual workflows**: Cannot scale with increasing detector requirements

### Urgency and Importance

As Azure monitoring needs grow, detector development is becoming a critical bottleneck. An intelligent, automated system that learns from historical patterns while maintaining human oversight can dramatically accelerate delivery while improving consistency and quality.

---

## Proposed Solution

### Core Concept

**maf-agents** leverages Microsoft Agent Framework's workflow orchestration capabilities to create a conversational, multi-agent system where each step in the detector lifecycle is handled by a specialized sub-workflow agent. The system is built entirely on Azure-native services, utilizing **Azure Repos** for source control and PR management, and **Azure Kusto** (Azure Data Explorer) for all data querying and analysis. The main orchestrator coordinates these agents through a sequential workflow with checkpoints, enabling state management, error recovery, and human approval gates.

### Key Differentiators

1. **Pattern Learning**: Analyzes historical PRs to extract naming conventions, code patterns, and best practices automatically
2. **Conversational Interface**: Natural language interaction guides users through complex workflows
3. **Human-in-the-Loop**: Critical approval gates ensure AI automation doesn't bypass necessary reviews
4. **End-to-End Automation**: From ETW input to customer-facing detector in a single workflow
5. **Context Awareness**: Maintains state through checkpoints, enabling resume after interruptions

### Why This Solution Will Succeed

- **Built on Microsoft Agent Framework**: Native integration with Azure services and proven orchestration patterns
- **Incremental Validation**: Each step validates before proceeding, catching errors early
- **Learning System**: Continuously improves by analyzing successful PR patterns
- **Developer-Friendly**: Conversational interface lowers barrier to entry for new team members

### High-Level Vision

A self-improving detector development assistant that handles 80% of implementation work while keeping engineers in control of critical decisions, ultimately becoming the standard tool for all detector development workflows.

---

## Target Users

### Primary User Segment: Azure Detector Engineers

**Profile**:
- Software engineers responsible for creating and maintaining Azure detectors
- 2-5 years experience with Azure services, Kusto queries, and ETW
- Comfortable with Python and Azure DevOps workflows
- Typically work in incident response, monitoring, or platform reliability teams

**Current Behaviors**:
- Manually query Kusto clusters to validate ETW schemas
- Review historical PRs for pattern guidance
- Create detector code following team conventions
- Submit PRs and wait for review/deployment
- Monitor detector effectiveness through Kusto queries

**Pain Points**:
- Repetitive context switching between tools
- Difficulty maintaining consistency across detectors
- Time-consuming schema validation and pattern matching
- Waiting for deployment confirmation before testing

**Goals**:
- Reduce time spent on repetitive detector development tasks
- Improve code consistency and quality
- Accelerate iteration cycles
- Focus on complex logic rather than boilerplate

### Secondary User Segment: Engineering Managers

**Profile**:
- Team leads overseeing detector development teams
- Responsible for delivery velocity and code quality
- Need visibility into detector development pipeline

**Pain Points**:
- Inconsistent detector quality across team members
- Difficulty onboarding new engineers to detector development
- Limited visibility into workflow bottlenecks

**Goals**:
- Standardize detector development practices
- Reduce onboarding time for new team members
- Increase team productivity and output quality

---

## Goals & Success Metrics

### Business Objectives

- **Reduce detector development cycle time by 70%** (from 6 hours to <2 hours for standard detectors)
- **Achieve 90% code pattern consistency** across detectors developed through the system
- **Enable 50% reduction in onboarding time** for new detector developers
- **Process 10+ detector workflows** successfully during POC phase

### User Success Metrics

- **Time to first detector commit**: <30 minutes from ETW input to PR creation
- **User approval turnaround**: <5 minutes for reviewing generated PRs
- **Deployment verification success rate**: >95% accurate detection of merged/deployed PRs
- **Results analysis quality**: >90% of Kusto query results correctly interpreted

### Key Performance Indicators (KPIs)

- **Workflow completion rate**: % of started workflows that reach production promotion
- **Error recovery rate**: % of workflows that successfully resume from checkpoints
- **Pattern match accuracy**: % of generated code that follows historical conventions
- **User satisfaction score**: Post-workflow survey rating (target: 4.5/5)
- **System availability**: Uptime and response time for conversational interface

---

## MVP Scope

### Core Features (Must Have)

- **ETW Input Collection Agent**: Conversationally collect providerGuid and ruleId from users
  - *Rationale*: Foundation for entire workflow; must validate inputs early

- **Kusto Schema Discovery Agent**: Query Azure Kusto cluster to identify common detectors and ETW schema
  - *Rationale*: Ensures detector built against correct schema; prevents downstream errors

- **Detector Code Generator Agent**: Create Azure repo branch, analyze historical PRs for patterns, generate detector files, and commit
  - *Rationale*: Core automation value; eliminates most manual coding work

- **User Approval Gate**: Present PR to user for review and wait for explicit approval
  - *Rationale*: Critical human-in-the-loop checkpoint; maintains quality control

- **Deployment Verification Agent**: Monitor merged PRs/deployments to confirm detector is live
  - *Rationale*: Closes loop on deployment; prevents proceeding with undeployed code

- **Results Analysis Agent**: Fetch and analyze detector results using Kusto queries
  - *Rationale*: Validates detector effectiveness before promotion

- **Production Promotion Agent**: Generate PR to make detector customer-facing using repo examples
  - *Rationale*: Completes end-to-end workflow; delivers final value

- **Sequential Orchestration**: Main workflow that coordinates all sub-agents in sequence
  - *Rationale*: Microsoft Agent Framework core pattern; ensures proper flow control

- **Checkpoint State Management**: Save workflow state at key milestones for recovery
  - *Rationale*: Enables resume after failures or interruptions; critical for long-running workflows

### Out of Scope for MVP

- Multi-detector batch processing
- Advanced error remediation (automated fix suggestions)
- Custom workflow configuration UI
- Integration with monitoring dashboards
- Automatic rollback on detector failures
- Support for non-ETW detector types
- Multi-language support (only Python)
- Performance optimization for large-scale queries

### MVP Success Criteria

**The MVP is successful if**:
- A user can complete the entire workflow from ETW input to production promotion in <2 hours
- The system generates detector code that matches historical patterns with >80% accuracy
- Checkpoint recovery works reliably when workflows are interrupted
- All 7 workflow steps execute successfully for at least 3 different detector types
- Users rate the conversational interface as "easy to use" (4/5 or higher)

---

## Post-MVP Vision

### Phase 2 Features

- **Parallel Workflow Execution**: Support multiple detector developments simultaneously
- **Advanced Pattern Learning**: ML-based code generation that improves with usage
- **Integration Testing Agent**: Automatically run detector tests before PR submission
- **Rollback Automation**: Detect failing detectors and initiate automated rollback
- **Custom Workflow Builder**: Allow users to configure workflow steps via UI
- **Detector Performance Insights**: Historical analysis of detector effectiveness

### Long-term Vision

Transform **maf-agents** into a comprehensive detector development platform that:
- Handles 90%+ of detector development workload autonomously
- Learns from production outcomes to improve code generation quality
- Expands to support multiple detector types (ETW, logs, metrics, traces)
- Integrates with incident response workflows for automated detector suggestions
- Becomes the standard tooling for all Azure detector development across the organization

### Expansion Opportunities

- **Generalization**: Adapt framework for other Azure automation workflows (resource provisioning, configuration management)
- **Enterprise Offering**: Package as a product for external Azure customers
- **Multi-Cloud Support**: Extend patterns to AWS CloudWatch and GCP monitoring
- **AI Governance**: Add explainability features for regulatory compliance

---

## Technical Considerations

### Platform Requirements

- **Target Platforms**: Linux (primary), Windows (secondary for local dev)
- **Python Version**: Python 3.10+
- **Required Azure Services**:
  - **Azure Repos** (part of Azure DevOps) - Source control, branch management, and PR workflows
  - **Azure Kusto (Azure Data Explorer)** - Data querying, schema discovery, and results analysis
  - Azure Pipelines (for deployment detection)
- **Performance Requirements**:
  - Sub-second response time for conversational turns
  - Azure Kusto query execution <30 seconds
  - Azure Repos PR creation <2 minutes

### Technology Preferences

- **Agent Framework**: Microsoft Agent Framework (Python SDK) - REQUIRED
- **Source Control**: Azure Repos (Azure DevOps Git) - REQUIRED
- **Data Platform**: Azure Kusto (Azure Data Explorer) - REQUIRED
- **Orchestration Pattern**: Sequential workflows with sub-workflow agents
- **State Management**: Microsoft Agent Framework checkpoint system
- **Conversational Interface**: Terminal/CLI for POC (Slack/Teams integration post-MVP)
- **Authentication**: Azure AD/Entra ID for service principals

### Architecture Considerations

- **Repository Structure**:
  - Monorepo with `/workflows` for agent definitions
  - `/agents` for sub-workflow implementations
  - `/shared` for common utilities (Kusto clients, Azure DevOps SDK)

- **Service Architecture**:
  - Stateless workflow execution engine
  - Checkpoint persistence to Azure Table Storage
  - Request/response pattern for agent communication

- **Integration Requirements**:
  - **Azure Repos via Azure DevOps REST API** for all repository and PR operations
  - **Azure Kusto Python SDK** for all data querying and analysis operations
  - Azure SDK for authentication and resource access
  - All integrations must use Azure-native APIs (no third-party alternatives)

- **Security/Compliance**:
  - Service principal with least-privilege access to DevOps and Kusto
  - Secret management via Azure Key Vault
  - Audit logging for all workflow actions
  - User approval required before any production changes

---

## Constraints & Assumptions

### Constraints

- **Budget**: POC phase only; no budget for production infrastructure
- **Timeline**: 2-3 weeks for POC development and validation
- **Resources**: Single developer working part-time on POC
- **Technical**:
  - Must use Microsoft Agent Framework (no alternative frameworks)
  - Must use Azure Repos for all source control operations (no GitHub, GitLab, etc.)
  - Must use Azure Kusto for all data querying and analysis (no alternative data platforms)
  - Kusto queries provided as static templates (no query generation in MVP)
  - Azure Repos must follow existing team conventions

### Key Assumptions

- Users have Azure Repos (Azure DevOps) and Azure Kusto access with appropriate permissions
- Historical PRs in Azure Repos follow consistent patterns suitable for learning
- Detector deployment process is observable through Azure DevOps APIs
- Azure Kusto cluster performance is sufficient for real-time queries
- Microsoft Agent Framework Python SDK is stable and well-documented
- ETW schema structure is relatively consistent across detectors
- User approval turnaround is <1 hour (workflow won't time out)

---

## Risks & Open Questions

### Key Risks

- **Framework Maturity**: Microsoft Agent Framework Python version may have limited examples or immature APIs
  - *Impact*: Could slow development or require workarounds
  - *Mitigation*: Deep dive into docs early; engage with Microsoft support if needed

- **Pattern Learning Quality**: Historical PRs may not contain sufficient signal for effective pattern extraction
  - *Impact*: Generated code may not match team conventions
  - *Mitigation*: Start with rule-based templates; iterate toward ML if data supports it

- **Azure Kusto Query Performance**: Large schema queries may exceed time limits
  - *Impact*: Workflow timeouts or poor user experience
  - *Mitigation*: Optimize Kusto queries upfront; implement caching if needed; leverage Kusto query best practices

- **Deployment Detection Reliability**: Merged PRs may not immediately reflect in deployment status
  - *Impact*: False positives or workflow stalls
  - *Mitigation*: Implement retry logic with exponential backoff

### Open Questions

- What authentication pattern should be used for long-running workflows (user token vs. service principal) for Azure Repos and Azure Kusto?
- How should the system handle partial failures (e.g., Azure Kusto query succeeds but Azure Repos PR creation fails)?
- Should checkpoint state include full conversation history or just workflow state?
- What's the expected format for "user approval" (CLI prompt, webhook callback, external system)?
- How will users provide Azure Kusto query templates (config files, inline, or hardcoded)?
- What Azure Kusto cluster and Azure Repos organization/project should be targeted?

### Areas Needing Further Research

- Microsoft Agent Framework checkpoint persistence best practices
- Azure Repos (Azure DevOps) API rate limits and retry policies
- Azure Kusto Python SDK error handling patterns and connection management
- Azure Kusto query optimization techniques for large datasets
- Conversational UX design for technical workflows
- PR pattern extraction techniques from Azure Repos history (AST parsing vs. regex vs. LLM-based)

---

## Appendices

### A. Research Summary

**Microsoft Agent Framework Documentation Review**:
- Core workflow concepts: Sequential orchestration, sub-workflows as agents, request/response patterns
- Checkpoint system supports state persistence and recovery
- Python SDK provides native Azure integration
- Recommended pattern: Main orchestrator with specialized sub-workflow agents

**Key Documentation References**:
- [Workflow Core Concepts](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/core-concepts/overview)
- [Sequential Orchestrations](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/orchestrations/sequential?pivots=programming-language-python)
- [Workflows as Agents](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/as-agents?pivots=programming-language-python)
- [Request and Response](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/request-and-response?pivots=programming-language-python)
- [Checkpoints](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/checkpoints?pivots=programming-language-python)

### C. References

**Core Technologies**:
- Microsoft Agent Framework Documentation: <https://learn.microsoft.com/en-us/agent-framework/>
- Azure Repos (Azure DevOps) REST API: <https://learn.microsoft.com/en-us/rest/api/azure/devops/>
- Azure Kusto (Azure Data Explorer) Documentation: <https://learn.microsoft.com/en-us/azure/data-explorer/>
- Azure Kusto Python SDK: <https://github.com/Azure/azure-kusto-python>
- ETW Overview: <https://learn.microsoft.com/en-us/windows/win32/etw/>

---

## Next Steps

### Immediate Actions

1. **Set up development environment**: Install Microsoft Agent Framework Python SDK, Azure Repos SDK, Azure Kusto Python SDK, and configure Azure authentication
2. **Configure Azure access**: Obtain credentials/service principal for Azure Repos and Azure Kusto cluster access
3. **Create project repository structure**: Initialize `/workflows`, `/agents`, `/shared` directories in Azure Repos following recommended patterns
4. **Implement prototype main orchestrator**: Sequential workflow skeleton that coordinates 7 sub-workflow agents
5. **Build first sub-agent (ETW Input Collection)**: Validate framework understanding and conversational pattern
6. **Obtain Azure Kusto query templates**: Get actual Kusto queries for schema discovery and results analysis from stakeholders
7. **Test Azure Repos integration**: Validate branch creation, PR submission, and deployment detection
8. **Test Azure Kusto integration**: Validate query execution, result parsing, and error handling
9. **Test checkpoint persistence**: Validate state management and recovery mechanisms
10. **Document learnings**: Capture framework quirks, Azure API patterns, and decision rationale for future reference

### PM Handoff

This Project Brief provides the full context for **maf-agents** - a Microsoft Agent Framework POC for automated Azure detector development. The brief outlines a conversational multi-agent workflow system with 7 specialized sub-agents orchestrated sequentially, featuring checkpoint-based state management, human-in-the-loop approval gates, and pattern learning from historical PRs.

**Please start in 'PRD Generation Mode'**, review the brief thoroughly to work with the user to create the PRD section by section as the template indicates, asking for any necessary clarification or suggesting improvements.
