# Story 2.3: Kusto Schema Discovery Agent Implementation

**Epic**: Epic 2: ETW Input Collection & Schema Discovery

## User Story

As a **detector engineer**,
I want **an agent that queries Kusto to discover existing detectors and retrieve the ETW schema**,
so that **I know my detector will use the correct schema and I can see related detectors**.

## Acceptance Criteria

1. `/agents/schema_discovery_agent.py` implements the Schema Discovery agent as a Microsoft Agent Framework sub-workflow
2. Agent retrieves providerGuid and ruleId from workflow state
3. Agent constructs Kusto query (from template) to find existing detectors matching providerGuid
4. Agent executes Kusto query using `KustoClientWrapper`
5. Agent parses query results to extract list of existing detector names and metadata
6. Agent constructs Kusto query (from template) to retrieve ETW schema definition for providerGuid
7. Agent executes schema query and parses results to extract schema fields
8. Agent stores existing detectors list and schema definition in workflow state
9. Agent presents findings to user conversationally (e.g., "Found 3 existing detectors: X, Y, Z. Schema has 12 fields.")
10. Agent integrates with main orchestrator as second workflow step after ETW Input Collection
11. Unit tests validate query construction and result parsing with mock Kusto responses
12. Integration test validates complete schema discovery with real Kusto cluster and sample ETW data

## Notes

This agent provides critical validation - ensuring the detector is built against the correct schema. The conversational feedback helps users understand what already exists.

## Related Documents

- PRD: docs/prd.md (Epic 2, Story 2.3)
- Architecture: docs/architecture.md
