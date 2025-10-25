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
