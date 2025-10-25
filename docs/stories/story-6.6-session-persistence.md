# Story 6.6: Session Persistence and Recovery

**Epic**: Epic 6: Production-Ready Next.js Frontend Integration

## User Story

As a **user**,
I want **my workflow session to persist when I refresh the page or close the browser**,
so that **I don't lose progress if my browser crashes or I navigate away accidentally**.

## Acceptance Criteria

1. **AC1**: Active workflow ID is saved to browser localStorage on workflow creation
2. **AC2**: Workflow state is restored from localStorage on page load if workflow ID exists
3. **AC3**: Backend API is queried to fetch latest workflow status on page restore
4. **AC4**: Chat message history is restored from backend data or localStorage
5. **AC5**: WorkflowStepper displays correct step based on restored state
6. **AC6**: Completed workflows are removed from localStorage after 24 hours
7. **AC7**: Failed workflows display restoration option with ability to start fresh
8. **AC8**: Multiple concurrent workflows are supported with session isolation

## Integration Verification

- **IV1**: Create workflow, advance to step 3, refresh page, verify state restores correctly
- **IV2**: Create workflow, close browser, reopen, verify workflow can be resumed
- **IV3**: Create 3 workflows, verify each maintains isolated state in localStorage
- **IV4**: Complete workflow, wait 24 hours (or manipulate timestamp), verify cleanup occurs

## Technical Notes

### LocalStorage Schema

```typescript
interface StoredWorkflowSession {
  workflowId: string;
  lastUpdated: string;
  currentStep: number;
  status: string;
  chatHistory?: ChatMessage[];
}

// Storage key pattern
const WORKFLOW_STORAGE_KEY = "maf-agents-workflow-{workflowId}";
const ACTIVE_WORKFLOWS_KEY = "maf-agents-active-workflows";
```

### Cleanup Strategy

- On app initialization, check all stored workflow sessions
- Remove sessions older than 24 hours for completed workflows
- Keep failed workflows for 7 days to allow recovery
- Keep active/running workflows indefinitely

### Session Recovery Flow

1. App loads → Check localStorage for active workflows
2. If found → Query backend `/api/workflows/{id}` for latest state
3. Compare backend state with localStorage
4. Use backend as source of truth; update localStorage
5. Restore UI state based on backend response

## Dependencies

- **Depends on**: Story 6.1 (Core Frontend Refactoring)
- **Depends on**: Story 6.2 (Backend REST API Integration)
- **Depends on**: Story 6.3 (WebSocket Integration)

## Related Documents

- PRD: docs/prd.md (Story 1.6)
- Workflow Context: client/src/components/providers/WorkflowProvider.tsx
