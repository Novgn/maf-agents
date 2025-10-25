# Story 2.4: Kusto Query Template Configuration

**Epic**: Epic 2: ETW Input Collection & Schema Discovery

## User Story

As a **developer**,
I want **Kusto query templates stored in configuration files**,
so that **queries can be easily modified without code changes**.

## Acceptance Criteria

1. `/config/kusto_queries.yaml` file created with template definitions
2. Template includes `find_existing_detectors` query with placeholders for providerGuid
3. Template includes `get_etw_schema` query with placeholders for providerGuid
4. Template includes `fetch_detector_results` query with placeholders for detector name and time range (for future use)
5. Query templates use parameterized format compatible with Kusto Python SDK
6. `/shared/kusto_client.py` implements `load_query_template(template_name, params)` method
7. Method replaces placeholders with actual values and returns executable query string
8. Unit tests validate template loading and parameter substitution
9. README documents how to add or modify query templates

## Notes

This configuration-based approach makes the system maintainable and allows non-developers to update queries as Kusto schemas evolve.

## Related Documents

- PRD: docs/prd.md (Epic 2, Story 2.4)
- Architecture: docs/architecture.md
