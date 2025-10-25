# Story 1.4: Main Workflow Orchestrator Skeleton

**Epic**: Epic 1: Foundation & Workflow Orchestration

## User Story

As a **developer**,
I want **a main orchestrator that coordinates workflow agents sequentially using Microsoft Agent Framework**,
so that **I can add agents incrementally and validate orchestration logic**.

## Acceptance Criteria

1. `/workflows/main_orchestrator.py` implements the main workflow class using Microsoft Agent Framework sequential orchestration pattern
2. Orchestrator defines placeholders for 7 sub-workflow agents (ETW Input, Schema Discovery, Code Generator, User Approval, Deployment Verification, Results Analysis, Production Promotion)
3. Orchestrator implements checkpoint save/load at workflow start, between agents, and at workflow completion
4. Orchestrator provides conversational interface (CLI prompts) for workflow initialization and progress updates
5. Orchestrator handles exceptions and errors gracefully with user-friendly messages
6. Workflow can be started with `python -m workflows.main_orchestrator` and executes placeholder agents in sequence
7. Unit test validates orchestrator calls agents in correct sequential order
8. Integration test validates checkpoint persistence between agent executions

## Notes

This is the central control point for the entire workflow. The skeleton created here will be progressively enhanced as agents are implemented in subsequent stories.

## Related Documents

- PRD: docs/prd.md (Epic 1, Story 1.4)
- Architecture: docs/architecture.md
