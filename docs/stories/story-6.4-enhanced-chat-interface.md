# Story 6.4: Enhanced Chat Interface with Backend Integration

**Epic**: Epic 6: Production-Ready Next.js Frontend Integration

## User Story

As a **user**,
I want **to interact with the detector triage agent through a production-quality chat interface**,
so that **I can naturally describe my detector requirements and receive guided assistance**.

## Acceptance Criteria

1. **AC1**: Chat messages are sent to backend triage agent via `submitInput` API call
2. **AC2**: Agent responses are received via WebSocket and displayed in chat interface
3. **AC3**: Chat interface supports markdown rendering for formatted agent responses
4. **AC4**: Message history is maintained in component state and persists during workflow session
5. **AC5**: Chat input is disabled with loading spinner while waiting for agent response
6. **AC6**: Long agent responses are properly formatted with scrollable message area
7. **AC7**: Timestamps are displayed for each message in human-readable format
8. **AC8**: Chat history scrolls to bottom automatically when new messages arrive

## Integration Verification

- **IV1**: Send chat message and verify it appears in backend workflow logs
- **IV2**: Trigger agent response from backend and verify it renders in UI with markdown formatting
- **IV3**: Send multiple rapid messages and verify UI handles queueing gracefully
- **IV4**: Verify chat history persists when navigating away and returning to workflow page

## Technical Notes

### Markdown Rendering

Use `react-markdown` library for rendering formatted agent responses:

```bash
npm install react-markdown
```

### Chat Message Structure

```typescript
interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  metadata?: {
    step?: number;
    data?: Record<string, any>;
  };
}
```

### Input Submission Format

```typescript
{
  input_type: "triage_message",
  data: {
    message: string;
  }
}
```

## Dependencies

- **Depends on**: Story 6.1 (Core Frontend Refactoring)
- **Depends on**: Story 6.2 (Backend REST API Integration)
- **Depends on**: Story 6.3 (WebSocket Integration)

## Related Documents

- PRD: docs/prd.md (Story 1.4)
- Chat Component: client/src/components/workflow/chat-interface.tsx
- Backend Triage Agent: workflows/detector_workflow.py
