# Story 4.1: Deployment Verification Agent Implementation

**Epic**: Epic 4: Deployment Verification & Results Analysis

## User Story

As a **detector engineer**,
I want **an agent that monitors my PR and notifies me when the detector is successfully deployed**,
so that **I know when to proceed with results analysis**.

## Acceptance Criteria

1. `/agents/deployment_verification_agent.py` implements the Deployment Verification agent as Microsoft Agent Framework sub-workflow
2. Agent retrieves PR ID from workflow state
3. Agent implements polling logic to check PR merge status via Azure Repos API (`get_pull_request_status`)
4. Agent polls every 30 seconds with maximum wait time of 60 minutes (configurable)
5. Agent detects when PR status changes to "completed" (merged)
6. Agent queries Azure Pipelines API to check if deployment pipeline triggered and completed successfully
7. Agent implements retry logic with exponential backoff for API calls per NFR10
8. Agent stores deployment status and timestamp in workflow state
9. Agent presents deployment confirmation to user conversationally (e.g., "PR merged and detector deployed successfully at 10:30 AM")
10. Agent handles timeout scenario gracefully (e.g., "Deployment not detected after 60 minutes. Please verify manually.")
11. Agent integrates with main orchestrator after User Approval Gate
12. Unit tests validate polling logic and status detection with mocks
13. Integration test validates deployment detection with simulated PR merge

## Notes

This agent closes a critical feedback loop - users need to know when their detector is actually deployed before they can validate results. The polling logic must be robust and informative.

## Related Documents

- PRD: docs/prd.md (Epic 4, Story 4.1)
- Architecture: docs/architecture.md
