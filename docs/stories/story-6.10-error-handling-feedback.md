# Story 6.10: Error Handling and User Feedback

**Epic**: Epic 6: Production-Ready Next.js Frontend Integration

## User Story

As a **user**,
I want **clear, actionable error messages and loading indicators throughout the application**,
so that **I understand what's happening and what to do when problems occur**.

## Acceptance Criteria

1. **AC1**: All API errors display user-friendly messages (no raw stack traces shown to user)
2. **AC2**: Network errors show "Connection failed - please check your network" message
3. **AC3**: Backend unavailable shows "Backend service unavailable - please try again later"
4. **AC4**: Workflow step failures display specific error with retry option
5. **AC5**: All async operations show loading spinners or progress indicators
6. **AC6**: Error boundary catches React errors and displays fallback UI with "Report Issue" button
7. **AC7**: Toast notifications are used for non-critical feedback (workflow created, action completed)
8. **AC8**: Critical errors are logged to browser console (dev) and Application Insights (prod)

## Integration Verification

- **IV1**: Stop backend server and verify user-friendly "service unavailable" message appears
- **IV2**: Trigger React component error and verify error boundary catches it with fallback UI
- **IV3**: Submit invalid ETW input data and verify validation error message is clear
- **IV4**: Check Application Insights logs in production for error tracking

## Technical Notes

### Error Boundary Component

```typescript
// client/src/components/ErrorBoundary.tsx
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
    // Log to Application Insights in production
    if (process.env.NODE_ENV === "production") {
      logErrorToAppInsights(error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallbackUI error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

### Error Message Mapping

```typescript
const ERROR_MESSAGES: Record<string, string> = {
  NETWORK_ERROR: "Connection failed. Please check your network and try again.",
  BACKEND_UNAVAILABLE: "Backend service is unavailable. Please try again later.",
  VALIDATION_ERROR: "Invalid input data. Please check your entries and try again.",
  TIMEOUT: "Request timed out. The server is taking too long to respond.",
  UNAUTHORIZED: "You are not authorized to perform this action.",
  NOT_FOUND: "The requested resource was not found.",
  WORKFLOW_FAILED: "Workflow execution failed. Please check the error details below.",
};

function getUserFriendlyError(error: Error): string {
  // Map technical errors to user-friendly messages
  if (error.message.includes("fetch")) return ERROR_MESSAGES.NETWORK_ERROR;
  if (error.message.includes("timeout")) return ERROR_MESSAGES.TIMEOUT;
  // ... more mappings
  return "An unexpected error occurred. Please try again.";
}
```

### Toast Notification Library

Install and configure toast notifications:

```bash
npm install sonner
```

```typescript
import { toast } from "sonner";

// Success notifications
toast.success("Workflow created successfully!");

// Error notifications
toast.error("Failed to submit input. Please try again.");

// Loading notifications
const toastId = toast.loading("Creating workflow...");
// ... later
toast.success("Workflow created!", { id: toastId });
```

### Loading States

Standard loading indicator:

```tsx
import { Loader2 } from "lucide-react";

<div className="flex items-center gap-2">
  <Loader2 className="h-4 w-4 animate-spin" />
  <span>Loading...</span>
</div>
```

## Dependencies

- **Depends on**: Story 6.1 (Core Frontend Refactoring)
- **Depends on**: Story 6.2 (Backend REST API Integration)

## Related Documents

- PRD: docs/prd.md (Story 1.10)
- Error Boundary: client/src/components/ErrorBoundary.tsx
- Root Layout: client/src/app/layout.tsx
