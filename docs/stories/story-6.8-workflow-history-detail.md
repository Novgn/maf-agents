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

---

## Tasks

### Task 1: Review API Client for Workflow Detail Endpoint
- [x] Reviewed existing API client methods
- [x] Identified need for detailed workflow data endpoint
- [x] Confirmed endpoint pattern: `/api/workflows/{id}/detail`

### Task 2: Add WorkflowDetail Interface to types.ts
- [x] Created WorkflowStepDetail interface for step execution data
- [x] Created WorkflowArtifacts interface for PR and results data
- [x] Created WorkflowInputData interface for ETW input data
- [x] Created complete WorkflowDetail interface
- [x] Added comprehensive JSDoc documentation

### Task 3: Add getWorkflowDetail Method to API Client
- [x] Added getWorkflowDetail method to APIClient class
- [x] Defined complete return type matching backend API
- [x] Configured endpoint: `/api/workflows/${workflowId}/detail`
- [x] Includes retry logic with exponential backoff
- [x] Returns detailed step, chat, artifact, and input data

### Task 4: Create Workflow Detail Page Route at /dashboard/workflow/[id]
- [x] Created dynamic route directory: client/src/app/dashboard/workflow/[id]
- [x] Created page.tsx component with Next.js 16 App Router
- [x] Implemented useParams hook to extract workflow ID
- [x] Added loading state with spinner
- [x] Added error state with fallback UI

### Task 5: Implement Workflow Summary Section with Status Badge
- [x] Created workflow summary card with header
- [x] Displayed workflow ID (full, monospace font)
- [x] Showed Provider GUID and Rule ID from input_data
- [x] Added creation and completion timestamps
- [x] Integrated status badge in page header with icons
- [x] Badge supports: starting, running, completed, failed states

### Task 6: Create Execution Timeline Component with Step Durations
- [x] Created execution timeline card section
- [x] Displayed all workflow steps in chronological order
- [x] Added step status icons (✓, ✗, spinner, clock)
- [x] Showed step number, name, and duration (formatted as Xm Ys)
- [x] Displayed step start timestamp
- [x] Showed error messages for failed steps
- [x] Added "No step data available" empty state

### Task 7: Display Chat Conversation History
- [x] Created chat history card section
- [x] Displayed messages in chronological order
- [x] Differentiated user vs agent messages with styling
- [x] User messages: blue background, right-aligned
- [x] Agent messages: gray background, left-aligned, markdown rendering
- [x] Showed role and timestamp for each message
- [x] Used ReactMarkdown for agent responses
- [x] Conditional rendering: only shows if chat_history exists

### Task 8: Show Generated Artifacts (PR Links, Results Analysis)
- [x] Created generated artifacts card section
- [x] Displayed PR URL with "View in Azure DevOps" external link
- [x] Showed PR number if available
- [x] Displayed results analysis summary with markdown formatting
- [x] Added icons for each artifact type (FileText, BarChart3)
- [x] Used border cards for each artifact
- [x] Conditional rendering: only shows if artifacts exist

### Task 9: Add Back to Dashboard Navigation Button
- [x] Added "Back to Dashboard" button in page header
- [x] Button uses ArrowLeft icon
- [x] Navigates to /dashboard using router.push
- [x] Positioned in top-left, status badge in top-right

### Task 10: Test and Validate Workflow Detail View
- [x] Run TypeScript type check (zero errors)
- [x] Run ESLint (zero errors)
- [x] Build production bundle successfully
- [x] Verified dynamic route registered correctly
- [x] Update story documentation with tasks and completion notes

---

## Dev Agent Record

### Status
**Current Status**: Ready for Review

### Agent/Model Used
- Model: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
- Agent: James (Full Stack Developer)

### Completion Notes
- All 10 tasks completed successfully
- Created comprehensive WorkflowDetail interface with supporting types
- Added getWorkflowDetail API method for fetching detailed workflow data
- Built complete workflow detail page at /dashboard/workflow/[id]
- Page includes all required sections: summary, timeline, chat, artifacts
- Status badge prominently displayed with icon animations
- Execution timeline shows all steps with durations and status icons
- Chat history with proper styling and markdown rendering for agent messages
- Generated artifacts section with external PR links and results analysis
- Back to Dashboard navigation button for easy return
- All timestamps formatted in human-readable format
- Error handling with fallback UI for missing/failed workflows
- TypeScript strict mode: Zero errors
- ESLint: Zero errors
- Production build: Successful (1097ms compilation)
- Dynamic route correctly registered as server-rendered
- All acceptance criteria met (AC1-AC8)

### File List
Files modified/created during this story:
- client/src/lib/types.ts (modified - added WorkflowDetail and related interfaces)
- client/src/lib/api-client.ts (modified - added getWorkflowDetail method)
- client/src/app/dashboard/workflow/[id]/page.tsx (created - workflow detail view page)

### Change Log
| Date | Change | Files Affected |
|------|--------|----------------|
| 2025-10-25 | Story tasks defined | story-6.8-workflow-history-detail.md |
| 2025-10-25 | Task 1: API client reviewed | api-client.ts |
| 2025-10-25 | Task 2: WorkflowDetail interfaces added | types.ts |
| 2025-10-25 | Task 3: getWorkflowDetail method added | api-client.ts |
| 2025-10-25 | Task 4-9: Workflow detail page created | page.tsx ([id]) |
| 2025-10-25 | Task 10: Validation complete, build succeeds | All files |
| 2025-10-25 | Story marked Ready for Review | story-6.8-workflow-history-detail.md |
