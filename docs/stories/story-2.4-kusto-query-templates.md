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

---

## Tasks

- [x] Review existing config/kusto_queries.yaml file
- [x] Update KustoClientWrapper to load templates from YAML
- [x] Implement _load_query_templates() class method with caching
- [x] Update load_query_template() to use template names
- [x] Update schema_discovery_agent to use template names
- [x] Write unit tests for template loading (6 new tests)
- [x] Document query template usage in README
- [x] Verify all tests pass (94 passed)

---

## Dev Agent Record

### Status
**Ready for Review** ✅

### Agent Model Used
- Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Completion Notes
- config/kusto_queries.yaml already existed with comprehensive templates
- Enhanced KustoClientWrapper to load templates from YAML file with class-level caching
- Updated load_query_template() method to accept template names instead of template strings
- Updated schema_discovery_agent to use template names ("find_existing_detectors", "get_etw_schema")
- All 9 acceptance criteria met
- 97% test coverage for kusto_client.py
- Added comprehensive documentation in README with usage examples
- All 94 tests pass (10 integration tests skipped without real Kusto cluster)

### File List
**Modified Files:**
- `shared/kusto_client.py` - Enhanced to load templates from YAML with caching
- `agents/schema_discovery_agent.py` - Updated to use template names
- `tests/unit/test_kusto_client.py` - Updated/added 6 tests for YAML template loading
- `tests/unit/test_schema_discovery_agent.py` - Removed hardcoded template references
- `README.md` - Added Kusto Query Templates section with documentation

### Change Log
- **2025-10-25**: Implemented YAML-based query template system
  - Added _load_query_templates() class method with caching to KustoClientWrapper
  - Updated load_query_template() to accept template names and load from YAML
  - Removed hardcoded query templates from schema_discovery_agent
  - Updated schema_discovery_agent to use template names
  - Added 6 unit tests for YAML template loading functionality
  - Documented template system in README with usage examples and instructions
  - All tests passing with 97% coverage for kusto_client.py
