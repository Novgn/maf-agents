# Story 2.2: Azure Kusto Client Wrapper Implementation

**Epic**: Epic 2: ETW Input Collection & Schema Discovery

## User Story

As a **developer**,
I want **a reusable Azure Kusto client wrapper with query execution and error handling**,
so that **all agents can query Kusto consistently and reliably**.

## Acceptance Criteria

1. `/shared/kusto_client.py` implements `KustoClientWrapper` class
2. Wrapper initializes Kusto client with cluster URL and database name from config
3. Wrapper implements `execute_query(query_string, timeout_seconds)` method
4. Wrapper handles Kusto query errors (syntax errors, timeouts, authentication failures) and raises specific exceptions
5. Wrapper implements retry logic with exponential backoff for transient failures
6. Wrapper logs all queries and results for debugging
7. Wrapper includes timeout enforcement (default 30 seconds per NFR2)
8. Unit tests validate error handling and retry logic with mocks
9. Integration test validates successful query execution against real Azure Kusto cluster

## Notes

This wrapper is critical infrastructure that all Kusto-dependent agents will rely on. Must be robust, well-tested, and handle all edge cases gracefully.

## Related Documents

- PRD: docs/prd.md (Epic 2, Story 2.2)
- Architecture: docs/architecture.md
