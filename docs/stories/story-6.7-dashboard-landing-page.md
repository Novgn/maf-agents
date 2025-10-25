# Story 6.7: Dashboard Landing Page

**Epic**: Epic 6: Production-Ready Next.js Frontend Integration

## User Story

As a **user**,
I want **a dashboard that shows all active workflows, system health, and workflow history**,
so that **I can monitor detector development activity and access past workflows**.

## Acceptance Criteria

1. **AC1**: Dashboard page (`/dashboard`) displays list of all workflows from backend API
2. **AC2**: Each workflow card shows: ID (truncated), status badge, current step, last updated timestamp
3. **AC3**: Workflows are filterable by status (all, running, completed, failed)
4. **AC4**: Clicking workflow card navigates to workflow detail view
5. **AC5**: System health panel shows: backend connection status, total workflows, active workflows
6. **AC6**: Dashboard auto-refreshes every 10 seconds to show latest data
7. **AC7**: "Create New Workflow" button navigates to `/workflow` page
8. **AC8**: Empty state message is displayed when no workflows exist

## Integration Verification

- **IV1**: Call `/api/workflows` endpoint and verify dashboard displays all workflows
- **IV2**: Create new workflow and verify it appears in dashboard within 10 seconds
- **IV3**: Filter workflows by "completed" status and verify only completed workflows show
- **IV4**: Verify system health panel shows accurate connection status and workflow counts

## Technical Notes

### Dashboard Layout

```
┌─────────────────────────────────────────────────────┐
│  Dashboard Header                [Create Workflow]  │
├─────────────────────────────────────────────────────┤
│  System Health Panel                                │
│  ● Connected | 12 Total | 3 Active                  │
├─────────────────────────────────────────────────────┤
│  Filters: [All] [Running] [Completed] [Failed]      │
├─────────────────────────────────────────────────────┤
│  Workflow Cards Grid                                │
│  ┌────────┐ ┌────────┐ ┌────────┐                  │
│  │ WF-123 │ │ WF-456 │ │ WF-789 │                  │
│  │ Running│ │Complete│ │ Failed │                  │
│  └────────┘ └────────┘ └────────┘                  │
└─────────────────────────────────────────────────────┘
```

### Workflow Card Component

```typescript
interface WorkflowCardProps {
  workflowId: string;
  status: string;
  currentStep: string;
  stepNumber: number;
  totalSteps: number;
  lastUpdated: string;
  onClick: () => void;
}
```

### Auto-Refresh Implementation

```typescript
useEffect(() => {
  const interval = setInterval(() => {
    fetchWorkflows();
  }, 10000); // 10 seconds

  return () => clearInterval(interval);
}, []);
```

## Dependencies

- **Depends on**: Story 6.1 (Core Frontend Refactoring)
- **Depends on**: Story 6.2 (Backend REST API Integration)

## Related Documents

- PRD: docs/prd.md (Story 1.7)
- Dashboard Route: client/src/app/dashboard/page.tsx
- Dashboard Components: client/src/components/dashboard/
