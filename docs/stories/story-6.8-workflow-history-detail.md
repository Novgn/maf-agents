# Story 6.8: Workflow History Detail View

**Epic**: Epic 6: Production-Ready Next.js Frontend Integration

## User Story

As a **user**,
I want **to view detailed information about completed workflows**,
so that **I can review past detector development sessions and access generated artifacts**.

## Acceptance Criteria

1. **AC1**: Workflow detail page (`/dashboard/workflow/[id]`) fetches workflow data from backend
2. **AC2**: Step-by-step execution timeline is displayed showing completion time for each step
3. **AC3**: Chat conversation history is displayed in chronological order
4. **AC4**: Generated PR links are displayed with click-through to Azure DevOps
5. **AC5**: ETW input data (providerGuid, ruleId) is displayed in summary section
6. **AC6**: Results analysis data from step 7 is formatted and displayed
7. **AC7**: Workflow status (completed/failed) is prominently displayed with status badge
8. **AC8**: "Back to Dashboard" button returns to dashboard page

## Integration Verification

- **IV1**: Complete full workflow, navigate to detail view, verify all steps are shown
- **IV2**: Verify chat history matches actual conversation from workflow execution
- **IV3**: Click PR link and verify it opens correct Azure DevOps pull request
- **IV4**: View failed workflow detail and verify error information is displayed

## Technical Notes

### Workflow Detail Layout

```
┌─────────────────────────────────────────────────────┐
│  [← Back to Dashboard]         Status: ● Completed  │
├─────────────────────────────────────────────────────┤
│  Workflow Summary                                   │
│  ID: abc123-def456                                  │
│  Provider GUID: {00000000-...}                      │
│  Rule ID: MyDetector_v1                             │
├─────────────────────────────────────────────────────┤
│  Execution Timeline                                 │
│  ✓ Step 1: Triage (2m 15s)                          │
│  ✓ Step 2: ETW Input (30s)                          │
│  ✓ Step 3: Schema Discovery (1m 45s)                │
│  ...                                                 │
├─────────────────────────────────────────────────────┤
│  Chat History                                       │
│  [User]: I want to detect ...                       │
│  [Agent]: Can you provide ...                       │
├─────────────────────────────────────────────────────┤
│  Generated Artifacts                                │
│  📄 Pull Request: #1234 [View in Azure DevOps]      │
│  📊 Results Analysis: 15 events detected             │
└─────────────────────────────────────────────────────┘
```

### Data Structure

```typescript
interface WorkflowDetail {
  workflow_id: string;
  status: string;
  created_at: string;
  completed_at: string;
  steps: Array<{
    step_number: number;
    step_name: string;
    status: string;
    started_at: string;
    completed_at: string;
    duration_seconds: number;
    error?: string;
  }>;
  chat_history: ChatMessage[];
  artifacts: {
    pr_url?: string;
    pr_number?: number;
    detector_code?: string;
    results_summary?: string;
  };
  input_data: {
    providerGuid: string;
    ruleId: string;
  };
}
```

## Dependencies

- **Depends on**: Story 6.1 (Core Frontend Refactoring)
- **Depends on**: Story 6.2 (Backend REST API Integration)
- **Depends on**: Story 6.7 (Dashboard Landing Page)

## Related Documents

- PRD: docs/prd.md (Story 1.8)
- Detail Route: client/src/app/dashboard/workflow/[id]/page.tsx
