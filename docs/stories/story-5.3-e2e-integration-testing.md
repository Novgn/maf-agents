# Story 5.3: End-to-End Workflow Integration Testing

**Epic**: Epic 5: Production Promotion & POC Validation

## User Story

As a **developer**,
I want **comprehensive integration tests that validate the complete workflow from ETW input to production promotion**,
so that **I can verify all 7 agents work together correctly**.

## Acceptance Criteria

1. `/tests/integration/test_e2e_workflow.py` implements end-to-end integration test
2. Test sets up test data: ETW providerGuid, ruleId, test Azure Repos repository, test Kusto cluster
3. Test executes complete workflow through main orchestrator with all 7 agents
4. Test validates checkpoint persistence at each step
5. Test simulates user approval inputs (approve PR, confirm results)
6. Test validates final state includes: generated PR, promotion PR, checkpoint history, results summary
7. Test validates workflow can resume from checkpoint if interrupted mid-flow
8. Test cleans up test data (branches, PRs) after completion
9. Test runs successfully against real Azure services (Kusto cluster, Azure Repos test repository)
10. Test execution time is within expected range (based on NFR timing requirements)
11. Test documents any deviations or issues discovered during execution

## Notes

This comprehensive E2E test is critical for validating the entire system works as designed. It's the ultimate proof that all components integrate correctly.

## Related Documents

- PRD: docs/prd.md (Epic 5, Story 5.3)
- Architecture: docs/architecture.md
