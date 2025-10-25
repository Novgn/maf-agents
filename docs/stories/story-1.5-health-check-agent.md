# Story 1.5: Health Check Agent and Framework Validation

**Epic**: Epic 1: Foundation & Workflow Orchestration

## User Story

As a **developer**,
I want **a simple health check agent that validates Azure connectivity and checkpoint recovery**,
so that **I can confirm the Microsoft Agent Framework setup is working correctly**.

## Acceptance Criteria

1. `/agents/health_check_agent.py` implements a minimal agent that performs health checks
2. Health check agent validates connectivity to Azure Kusto cluster (simple query like `print "Hello"`)
3. Health check agent validates connectivity to Azure Repos (fetch repository metadata)
4. Health check agent validates checkpoint save/load by creating and restoring a test checkpoint
5. Health check agent returns status report with success/failure for each validation
6. Main orchestrator can invoke health check agent as first step in workflow
7. CLI displays health check results in conversational format
8. Integration test validates successful health check execution with real Azure services

## Notes

This health check validates the entire foundation before building more complex agents. If this passes, we know authentication, Azure connectivity, and checkpoint system are working.

## Related Documents

- PRD: docs/prd.md (Epic 1, Story 1.5)
- Architecture: docs/architecture.md
