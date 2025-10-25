# Story 1.3: Checkpoint Persistence System Implementation

**Epic**: Epic 1: Foundation & Workflow Orchestration

## User Story

As a **developer**,
I want **a checkpoint system that saves and restores workflow state to Azure Table Storage**,
so that **workflows can resume after interruptions or failures**.

## Acceptance Criteria

1. `/shared/checkpoint.py` module implements `CheckpointManager` class
2. `CheckpointManager.save_checkpoint(workflow_id, state_dict)` persists state to Azure Table Storage
3. `CheckpointManager.load_checkpoint(workflow_id)` retrieves state from Azure Table Storage
4. `CheckpointManager.list_checkpoints()` returns all checkpoints for a workflow
5. Checkpoint state includes: workflow ID, timestamp, current agent/step, ETW inputs, PR URLs, and any intermediate results
6. Azure Table Storage connection configured via environment variable or config
7. Unit tests validate save, load, and list operations with mock or test table
8. Integration test validates round-trip persistence to real Azure Table Storage

## Notes

This is a core differentiator of the POC - the checkpoint system enables workflow resilience and recovery. Must be robust and well-tested.

## Related Documents

- PRD: docs/prd.md (Epic 1, Story 1.3)
- Architecture: docs/architecture.md
