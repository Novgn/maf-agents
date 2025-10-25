# Story 3.5: User Approval Gate Implementation

**Epic**: Epic 3: Detector Code Generation & PR Management

## User Story

As a **detector engineer**,
I want **the workflow to pause and wait for my explicit approval of the generated PR**,
so that **I maintain control over what gets deployed**.

## Acceptance Criteria

1. `/agents/approval_gate_agent.py` implements the User Approval Gate agent as Microsoft Agent Framework sub-workflow
2. Agent retrieves PR URL from workflow state
3. Agent presents PR details to user conversationally (PR URL, files changed, summary)
4. Agent prompts user: "Please review the PR. Type 'approve' to continue or 'reject' to cancel workflow."
5. Agent waits for user input (blocking operation)
6. If user approves, agent proceeds and returns success status
7. If user rejects, agent cancels workflow and exits gracefully with cancellation message
8. Agent saves checkpoint before waiting for approval (enables resume if process interrupted)
9. Agent integrates with main orchestrator after PR Creation agent
10. Unit tests validate approval and rejection logic with simulated inputs
11. Integration test validates approval gate pauses workflow and resumes correctly

## Notes

This is the critical human-in-the-loop control point. Users must feel confident that they maintain control and the system won't proceed without explicit approval.

## Related Documents

- PRD: docs/prd.md (Epic 3, Story 3.5)
- Architecture: docs/architecture.md
