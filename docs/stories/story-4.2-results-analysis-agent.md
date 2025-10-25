# Story 4.2: Results Analysis Agent Implementation

**Epic**: Epic 4: Deployment Verification & Results Analysis

## User Story

As a **detector engineer**,
I want **an agent that fetches detector results from Kusto and analyzes their effectiveness**,
so that **I can validate the detector is working before promoting to production**.

## Acceptance Criteria

1. `/agents/results_analysis_agent.py` implements the Results Analysis agent as Microsoft Agent Framework sub-workflow
2. Agent retrieves detector name and deployment timestamp from workflow state
3. Agent constructs Kusto query (from template) to fetch detector results for recent time window (e.g., last 1 hour)
4. Agent executes query using `KustoClientWrapper`
5. Agent parses query results to extract key metrics (number of events detected, error rate, false positive indicators)
6. Agent analyzes results and generates summary (e.g., "Detector found 15 events in last hour. No errors detected.")
7. Agent presents results conversationally with key findings highlighted
8. Agent prompts user: "Do the results look correct? Type 'yes' to proceed or 'no' to investigate."
9. Agent waits for user confirmation (blocking operation)
10. If user confirms, agent proceeds to next step. If user declines, agent pauses workflow for investigation
11. Agent stores results summary in workflow state
12. Agent integrates with main orchestrator after Deployment Verification
13. Unit tests validate query construction and result parsing with mock Kusto responses
14. Integration test validates results analysis with real Kusto detector data

## Notes

This is the validation checkpoint before production promotion. The analysis must be clear enough for users to make informed decisions about detector quality.

## Related Documents

- PRD: docs/prd.md (Epic 4, Story 4.2)
- Architecture: docs/architecture.md
