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

---

## Tasks

### Task 1: Create Dashboard Components Directory and WorkflowCard Component
- [x] Create client/src/components/dashboard directory
- [x] Create workflow-card.tsx component
- [x] Implement WorkflowCardProps interface with all required fields
- [x] Add status badge rendering with icons (running, completed, failed)
- [x] Implement human-readable timestamp formatting (Just now, Xm ago, Xh ago)
- [x] Add hover effects and click handler
- [x] Display workflow ID (truncated to 8 chars), status, step progress

### Task 2: Create SystemHealthPanel Component
- [x] Create system-health-panel.tsx component
- [x] Show backend connection status (Connected/Disconnected) with CheckCircle2/XCircle icons
- [x] Display total workflows count
- [x] Display active workflows count (running + starting)
- [x] Add loading states with Loader2 spinner
- [x] Use Card component with horizontal layout and dividers

### Task 3: Create Dashboard Page with Workflow List
- [x] Create client/src/app/dashboard/page.tsx
- [x] Implement fetchWorkflows function using apiClient.listWorkflows()
- [x] Add workflows state with WorkflowSummary interface
- [x] Display workflow cards in responsive grid (1/2/3 columns)
- [x] Add "Create New Workflow" button navigating to /workflow
- [x] Integrate SystemHealthPanel component
- [x] Add loading state during initial fetch

### Task 4: Implement Workflow Filtering by Status
- [x] Add filterStatus state (all, running, completed, failed)
- [x] Create filter buttons with active state styling
- [x] Show count badges on filter buttons
- [x] Implement filteredWorkflows computed value
- [x] Update grid to display filtered workflows

### Task 5: Add Auto-Refresh Functionality
- [x] Implement useEffect with setInterval for 10-second refresh
- [x] Call fetchWorkflows on interval
- [x] Clean up interval on component unmount
- [x] Ensure initial fetch happens on mount

### Task 6: Add Empty State and Loading States
- [x] Create loading state with Loader2 spinner and message
- [x] Create empty state with Inbox icon for "No workflows yet"
- [x] Create filtered empty state for "No {status} workflows"
- [x] Add "Create New Workflow" button in empty state
- [x] Handle all three states: loading, empty, data

### Task 7: Update Root Page Link to Point to Dashboard
- [x] Update client/src/app/page.tsx "View All" link
- [x] Change href from "/workflow" to "/dashboard"
- [x] Verify link navigates to dashboard page

### Task 8: Test Dashboard Integration and Update Story Documentation
- [x] Run TypeScript type check (zero errors)
- [x] Run ESLint (zero errors)
- [x] Build production bundle successfully
- [x] Update story documentation with tasks, completion notes, change log

---

## Dev Agent Record

### Status
**Current Status**: Ready for Review

### Agent/Model Used
- Model: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
- Agent: James (Full Stack Developer)

### Completion Notes
- All 8 tasks completed successfully
- Dashboard page created at /dashboard with full workflow list
- Workflow filtering by status (all, running, completed, failed) implemented
- Auto-refresh every 10 seconds ensures latest data
- System health panel shows backend connection and workflow counts
- Empty states and loading states provide good UX
- WorkflowCard component shows status badges, step progress, human-readable timestamps
- Click on card navigates to workflow detail view
- Root page "View All" link updated to point to dashboard
- TypeScript strict mode: Zero errors
- ESLint: Zero errors
- Production build: Successful (1084ms compilation)
- All acceptance criteria met (AC1-AC8)

### File List
Files modified/created during this story:
- client/src/components/dashboard/workflow-card.tsx (created - workflow card component with status badges and timestamps)
- client/src/components/dashboard/system-health-panel.tsx (created - system health panel showing backend status and workflow counts)
- client/src/app/dashboard/page.tsx (created - dashboard page with workflow list, filtering, and auto-refresh)
- client/src/app/page.tsx (modified - updated "View All" link to point to /dashboard)

### Change Log
| Date | Change | Files Affected |
|------|--------|----------------|
| 2025-10-25 | Story tasks defined | story-6.7-dashboard-landing-page.md |
| 2025-10-25 | Task 1: WorkflowCard component created | workflow-card.tsx |
| 2025-10-25 | Task 2: SystemHealthPanel component created | system-health-panel.tsx |
| 2025-10-25 | Task 3: Dashboard page created | page.tsx (dashboard) |
| 2025-10-25 | Task 4: Workflow filtering implemented | page.tsx (dashboard) |
| 2025-10-25 | Task 5: Auto-refresh functionality added | page.tsx (dashboard) |
| 2025-10-25 | Task 6: Empty and loading states added | page.tsx (dashboard) |
| 2025-10-25 | Task 7: Root page link updated | page.tsx (root) |
| 2025-10-25 | Task 8: Validation complete, build succeeds | All files |
| 2025-10-25 | Story marked Ready for Review | story-6.7-dashboard-landing-page.md |
