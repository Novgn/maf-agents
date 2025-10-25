# Story 2.1: ETW Input Collection Agent Implementation

**Epic**: Epic 2: ETW Input Collection & Schema Discovery

## User Story

As a **detector engineer**,
I want **a conversational agent that collects and validates my ETW providerGuid and ruleId**,
so that **I can provide detector requirements in a natural, guided way**.

## Acceptance Criteria

1. `/agents/etw_input_agent.py` implements the ETW Input Collection agent as a Microsoft Agent Framework sub-workflow
2. Agent prompts user conversationally for providerGuid (GUID format validation)
3. Agent prompts user for ruleId (string/integer validation)
4. Agent validates providerGuid format (valid GUID with hyphens)
5. Agent validates ruleId is not empty
6. Agent stores validated ETW inputs in workflow state for downstream agents
7. Agent provides helpful error messages for invalid inputs and re-prompts
8. Agent integrates with main orchestrator as the first workflow step
9. Unit tests validate input validation logic with valid and invalid inputs
10. Integration test validates conversational flow with simulated user inputs

## Notes

This is the first real workflow agent that users will interact with. The conversational UX is critical - it should feel natural and helpful, not robotic.

## Related Documents

- PRD: docs/prd.md (Epic 2, Story 2.1)
- Architecture: docs/architecture.md

---

## Tasks

- [x] Create agents/etw_input_agent.py with ChatAgent implementation
- [x] Implement validation functions for providerGuid (GUID format) and ruleId
- [x] Integrate ETW Input Agent into workflow executor
- [x] Write unit tests for validation logic (27 tests)
- [x] Write integration tests for conversational flow (7 tests)
- [x] Verify all tests pass

---

## Dev Agent Record

### Status
**Ready for Review** ✅

### Agent Model Used
- Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Completion Notes
- Implemented ETW Input Collection Agent using Microsoft Agent Framework's `ChatAgent` class
- Agent provides conversational UX for collecting providerGuid and ruleId from users
- Validation functions ensure proper GUID format (with hyphens) and non-empty rule ID
- Agent supports both conversational flow and pre-populated inputs (for automation)
- Integrated agent into workflow as the first step (etw_input_collection_executor)
- All 10 acceptance criteria met
- 100% test coverage for etw_input_agent.py
- All 58 tests pass (including existing tests)

### File List
**New Files:**
- `agents/etw_input_agent.py` - ETW Input Collection Agent implementation
- `tests/unit/test_etw_input_agent.py` - Unit tests for validation logic
- `tests/integration/test_etw_input_flow.py` - Integration tests for conversational flow
- `tests/integration/__init__.py` - Integration tests package

**Modified Files:**
- `workflows/detector_workflow.py` - Updated etw_input_collection_executor to use new agent

### Change Log
- **2025-10-25**: Initial implementation of ETW Input Collection Agent
  - Created `ETWInputAgent` class using Microsoft Agent Framework
  - Implemented `validate_provider_guid()` with GUID format validation
  - Implemented `validate_rule_id()` with empty check validation
  - Created `validate_etw_input()` tool function for agent
  - Updated workflow executor to use conversational agent
  - Added 27 unit tests covering all validation scenarios
  - Added 7 integration tests for conversational flows
  - All tests passing with 100% coverage for agent code
