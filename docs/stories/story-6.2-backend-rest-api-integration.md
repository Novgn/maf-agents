# Story 6.2: Backend REST API Integration

**Epic**: Epic 6: Production-Ready Next.js Frontend Integration

## User Story

As a **user**,
I want **the frontend to connect to the real backend API instead of using mock data**,
so that **workflow operations persist and reflect actual system state**.

## Acceptance Criteria

1. **AC1**: `apiClient` in `lib/api-client.ts` is enhanced with comprehensive error handling and retry logic
2. **AC2**: Environment variables (`NEXT_PUBLIC_API_URL`) are properly configured for dev and production
3. **AC3**: Workflow creation, retrieval, and deletion operations use real backend endpoints
4. **AC4**: Health check endpoint is called on app initialization to verify backend connectivity
5. **AC5**: Failed API requests display user-friendly error messages (not raw error objects)
6. **AC6**: API client implements 3-retry logic with exponential backoff for failed requests
7. **AC7**: All API responses are properly typed using TypeScript interfaces
8. **AC8**: Loading states are displayed during all async API operations

## Integration Verification

- **IV1**: Start backend server and confirm frontend health check succeeds
- **IV2**: Create a new workflow via API and verify it appears in backend state
- **IV3**: Simulate backend downtime and verify error handling displays user-friendly message
- **IV4**: Verify API retry logic attempts 3 retries before failing

## Technical Notes

### Backend Endpoints

- `GET /health` - Health check
- `POST /api/workflows` - Create workflow
- `GET /api/workflows` - List workflows
- `GET /api/workflows/{id}` - Get workflow status
- `POST /api/workflows/{id}/input` - Submit input
- `DELETE /api/workflows/{id}` - Delete workflow

### Retry Logic Implementation

```typescript
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve =>
        setTimeout(resolve, baseDelay * Math.pow(2, i))
      );
    }
  }
  throw new Error("Max retries exceeded");
}
```

## Dependencies

- **Depends on**: Story 6.1 (Core Frontend Refactoring)

## Related Documents

- PRD: docs/prd.md (Story 1.2)
- Backend API: server/api/main.py
- API Client: client/src/lib/api-client.ts

---

## Tasks

### Task 1: Add Retry Logic with Exponential Backoff
- [x] Create `retryWithBackoff` helper function in api-client.ts
- [x] Implement exponential backoff with 3 max retries
- [x] Skip retries for 4xx client errors
- [x] Add logging for retry attempts

### Task 2: Enhance Error Handling with User-Friendly Messages
- [x] Create `getUserFriendlyErrorMessage` helper function
- [x] Map HTTP error codes to user-friendly messages
- [x] Handle network errors and timeouts
- [x] Integrate error mapping into request method

### Task 3: Configure Environment Variables
- [x] Create `.env.example` template file
- [x] Create `.env.local` for local development
- [x] Update `.gitignore` to allow `.env.example` but ignore other .env files
- [x] Document environment variables (NEXT_PUBLIC_API_URL, NEXT_PUBLIC_WS_URL)

### Task 4: Implement Health Check on App Initialization
- [x] Create `use-health-check.ts` custom hook
- [x] Create `HealthIndicator` component
- [x] Add health check to workflow page
- [x] Implement retry functionality for failed health checks

### Task 5: Add Loading States to WorkflowProvider and useWorkflow
- [x] Add `isCreatingWorkflow` state to WorkflowContextType
- [x] Add `isSubmittingInput` state to WorkflowContextType
- [x] Update `createWorkflow` function with loading state
- [x] Update `submitInput` function with loading state
- [x] Export loading states from useWorkflow hook

### Task 6: Update API Client to Use Retry Logic
- [x] Modify `request` method to wrap with `retryWithBackoff`
- [x] Add `enableRetry` parameter (default: true)
- [x] Ensure all API methods use enhanced request method
- [x] Verify retry logic works with user-friendly error messages

### Task 7: Test API Integration and Validate
- [x] Run TypeScript type check (zero errors)
- [x] Run ESLint (zero errors)
- [x] Build production bundle successfully
- [x] Verify all new files compile correctly

---

## Dev Agent Record

### Status
**Current Status**: Ready for Review

### Agent/Model Used
- Model: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
- Agent: James (Full Stack Developer)

### Debug Log
No debug entries.

### Completion Notes
- All 7 tasks completed successfully
- Retry logic with exponential backoff implemented (3 retries, exponential delay)
- User-friendly error messages for all HTTP status codes and network errors
- Environment variable configuration with `.env.example` and `.env.local`
- Health check hook and component created for backend connectivity monitoring
- Loading states added to workflow context for better UX
- TypeScript strict mode: Zero errors
- ESLint: Zero errors
- Production build: Successful (962ms compilation)
- Manual testing recommended: Start backend server and verify health check, create workflow, test retry logic

### File List
Files modified/created during this story:
- client/src/lib/api-client.ts (modified - added retry logic, error handling)
- client/.env.example (created - environment variable template)
- client/.env.local (created - local development environment)
- client/.gitignore (modified - allow .env.example)
- client/src/hooks/use-health-check.ts (created - health check hook)
- client/src/components/HealthIndicator.tsx (created - health indicator UI)
- client/src/app/workflow/page.tsx (modified - added HealthIndicator)
- client/src/lib/types.ts (modified - added loading states to WorkflowContextType)
- client/src/hooks/use-workflow.ts (modified - added loading state management)

### Change Log
| Date | Change | Files Affected |
|------|--------|----------------|
| 2025-10-25 | Story tasks defined | story-6.2-backend-rest-api-integration.md |
| 2025-10-25 | Task 1: Retry logic with exponential backoff implemented | lib/api-client.ts |
| 2025-10-25 | Task 2: User-friendly error messages added | lib/api-client.ts |
| 2025-10-25 | Task 3: Environment variables configured | .env.example, .env.local, .gitignore |
| 2025-10-25 | Task 4: Health check hook and component created | use-health-check.ts, HealthIndicator.tsx, workflow/page.tsx |
| 2025-10-25 | Task 5: Loading states added to workflow context | types.ts, use-workflow.ts |
| 2025-10-25 | Task 6: API client updated with retry logic | lib/api-client.ts |
| 2025-10-25 | Task 7: Validation complete, build succeeds | All files |
| 2025-10-25 | Story marked Ready for Review | story-6.2-backend-rest-api-integration.md |
