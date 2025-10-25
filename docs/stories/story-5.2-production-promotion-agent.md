# Story 5.2: Production Promotion Agent Implementation

**Epic**: Epic 5: Production Promotion & POC Validation

## User Story

As a **detector engineer**,
I want **an agent that generates a PR to promote my detector to customer-facing status**,
so that **the detector can be enabled for production use following team conventions**.

## Acceptance Criteria

1. `/agents/production_promotion_agent.py` implements the Production Promotion agent as Microsoft Agent Framework sub-workflow
2. Agent retrieves detector name and results summary from workflow state
3. Agent invokes `PromotionPatternAnalyzer` to extract production promotion patterns
4. Agent generates configuration changes to enable detector for customer-facing (e.g., feature flag update, config file modification)
5. Agent creates new branch in Azure Repos (e.g., `detector/production-{detector-name}`)
6. Agent commits promotion changes with descriptive message (e.g., "Promote detector {name} to production")
7. Agent creates PR with title and description following promotion patterns
8. Agent presents promotion PR URL to user conversationally
9. Agent stores promotion PR details in workflow state
10. Agent marks workflow as complete and saves final checkpoint
11. Agent integrates with main orchestrator as final step after Results Analysis
12. Unit tests validate promotion change generation with mock patterns
13. Integration test validates complete production promotion workflow in test repository

## Notes

This is the final step in the end-to-end workflow. Successfully completing this step means the detector is ready for production deployment and customer use.

## Related Documents

- PRD: docs/prd.md (Epic 5, Story 5.2)
- Architecture: docs/architecture.md
