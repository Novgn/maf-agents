# Story 3.4: Azure Repos Branch and PR Creation Agent

**Epic**: Epic 3: Detector Code Generation & PR Management

## User Story

As a **detector engineer**,
I want **an agent that creates a branch, commits my generated code, and submits a PR**,
so that **I can review the code in Azure Repos before deployment**.

## Acceptance Criteria

1. `/agents/pr_creation_agent.py` implements the PR Creation agent as Microsoft Agent Framework sub-workflow
2. Agent generates unique branch name (e.g., `detector/etw-{providerGuid}-{timestamp}`)
3. Agent creates branch in Azure Repos from main/master branch
4. Agent commits generated detector files to branch with descriptive commit message
5. Agent creates PR with title following pattern conventions (e.g., "Add detector for ETW {providerGuid}")
6. Agent generates PR description including ETW details, schema summary, and generated files list
7. Agent stores PR ID and URL in workflow state
8. Agent presents PR URL to user conversationally (e.g., "PR created: https://dev.azure.com/.../pullrequests/123")
9. Agent integrates with main orchestrator after Code Generator agent
10. Unit tests validate branch naming, commit message, and PR description generation
11. Integration test validates complete branch/commit/PR workflow in test Azure Repos repository

## Notes

This agent bridges the gap between code generation and review - it handles all the version control mechanics so users can focus on reviewing the actual code.

## Related Documents

- PRD: docs/prd.md (Epic 3, Story 3.4)
- Architecture: docs/architecture.md
