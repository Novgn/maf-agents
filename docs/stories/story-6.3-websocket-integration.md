# Story 6.3: WebSocket Integration for Real-Time Updates

**Epic**: Epic 6: Production-Ready Next.js Frontend Integration

## User Story

As a **user**,
I want **to receive real-time workflow status updates without refreshing the page**,
so that **I can see workflow progress as it happens**.

## Acceptance Criteria

1. **AC1**: WebSocket connection is established when a workflow is created or loaded
2. **AC2**: Real-time workflow status updates (step changes, completions, failures) are received via WebSocket
3. **AC3**: WebSocket messages update the `WorkflowContext` state triggering UI re-renders
4. **AC4**: WebSocket connection implements automatic reconnection with exponential backoff (max 30 seconds)
5. **AC5**: Connection status indicator shows "Connected" (green) or "Disconnected" (gray) in UI
6. **AC6**: WebSocket cleanup occurs when component unmounts or workflow changes
7. **AC7**: Failed WebSocket connections fall back to periodic polling (every 5 seconds)
8. **AC8**: WebSocket message parsing errors are logged and don't crash the application

## Integration Verification

- **IV1**: Connect to backend and verify WebSocket establishes connection (check browser DevTools)
- **IV2**: Trigger workflow step change from backend and verify UI updates in real-time
- **IV3**: Simulate network interruption and verify automatic reconnection occurs
- **IV4**: Close backend WebSocket server and verify fallback to polling activates

## Technical Notes

### WebSocket Endpoint

- `ws://localhost:8000/ws/workflows/{workflow_id}` (dev)
- `wss://<azure-endpoint>/ws/workflows/{workflow_id}` (prod)

### WebSocket Message Types

```typescript
interface WebSocketMessage {
  type: "workflow_update" | "workflow_complete" | "workflow_failed" | "step_update";
  workflow_id: string;
  status: string;
  step_number?: number;
  current_step?: string;
  data?: Record<string, any>;
  error?: string;
}
```

### Reconnection Strategy

- Initial delay: 1 second
- Max delay: 30 seconds
- Exponential backoff multiplier: 2x
- Fallback to polling after 3 failed reconnection attempts

## Dependencies

- **Depends on**: Story 6.1 (Core Frontend Refactoring)
- **Depends on**: Story 6.2 (Backend REST API Integration)

## Related Documents

- PRD: docs/prd.md (Story 1.3)
- Backend WebSocket: server/api/main.py
- WebSocket Client: client/src/lib/api-client.ts

---

## Tasks

### Task 1: Enhance WebSocket Message Type Definitions
- [x] Add `WebSocketMessageType` type to types.ts
- [x] Create `WebSocketMessage` interface with proper typing
- [x] Include all message types (workflow_update, workflow_complete, workflow_failed, step_update)
- [x] Document all fields with JSDoc

### Task 2: Implement WebSocket Manager with Reconnection
- [x] Create `WebSocketManager` class in websocket-manager.ts
- [x] Implement exponential backoff reconnection logic
- [x] Add configurable max reconnect attempts (default: 3)
- [x] Implement exponential delay (1s, 2s, 4s... up to 30s max)
- [x] Add proper error handling and logging

### Task 3: Add Fallback to Polling
- [x] Implement polling mechanism after max reconnect attempts
- [x] Use existing `getWorkflowStatus` API endpoint
- [x] Set polling interval to 5 seconds
- [x] Convert REST API response to WebSocket message format
- [x] Add cleanup for polling timers

### Task 4: Improve WebSocket Error Handling
- [x] Add try-catch for JSON parsing errors
- [x] Log parsing errors without crashing app
- [x] Log raw message on parse failure for debugging
- [x] Handle WebSocket connection errors gracefully

### Task 5: Update use-workflow Hook
- [x] Replace `createWorkflowWebSocket` with `WebSocketManager`
- [x] Add `isReconnecting` state
- [x] Add `isUsingPolling` state
- [x] Update callbacks for reconnection and polling events
- [x] Export new state variables from hook

### Task 6: Enhance Connection Status Indicator
- [x] Update workflow page to use new connection states
- [x] Show "Connected" (green) when WebSocket is open
- [x] Show "Reconnecting..." (yellow with spinner) during reconnection
- [x] Show "Polling Mode" (blue) when using fallback polling
- [x] Show "Disconnected" (gray) when no connection

### Task 7: Test and Validate
- [x] Run TypeScript type check (zero errors)
- [x] Run ESLint (zero errors)
- [x] Build production bundle successfully
- [x] Verify WebSocket cleanup on unmount

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
- WebSocket reconnection with exponential backoff implemented (max 3 attempts)
- Automatic fallback to polling after failed reconnections (5-second interval)
- Enhanced connection status UI showing all connection states
- Proper WebSocket cleanup on component unmount
- Robust error handling for message parsing
- TypeScript strict mode: Zero errors
- ESLint: Zero errors
- Production build: Successful (974ms compilation)
- Manual testing recommended: Test reconnection by stopping/starting backend, verify polling fallback

### File List
Files modified/created during this story:
- client/src/lib/types.ts (modified - added WebSocket message types, reconnection states)
- client/src/lib/websocket-manager.ts (created - WebSocket manager with reconnection and polling)
- client/src/hooks/use-workflow.ts (modified - integrated WebSocketManager, added reconnection states)
- client/src/app/workflow/page.tsx (modified - enhanced connection status indicator)

### Change Log
| Date | Change | Files Affected |
|------|--------|----------------|
| 2025-10-25 | Story tasks defined | story-6.3-websocket-integration.md |
| 2025-10-25 | Task 1: WebSocket message types enhanced | types.ts |
| 2025-10-25 | Task 2: WebSocketManager class created | websocket-manager.ts |
| 2025-10-25 | Task 3: Polling fallback implemented | websocket-manager.ts |
| 2025-10-25 | Task 4: Error handling improved | websocket-manager.ts |
| 2025-10-25 | Task 5: use-workflow hook updated | use-workflow.ts |
| 2025-10-25 | Task 6: Connection status indicator enhanced | workflow/page.tsx |
| 2025-10-25 | Task 7: Validation complete, build succeeds | All files |
| 2025-10-25 | Story marked Ready for Review | story-6.3-websocket-integration.md |
