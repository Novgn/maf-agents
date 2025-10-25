# Story 6.5: Workflow Step Components Integration

**Epic**: Epic 6: Production-Ready Next.js Frontend Integration

## User Story

As a **user**,
I want **all 9 workflow steps to display appropriate UI components connected to the backend**,
so that **I can complete the entire detector development workflow through the web interface**.

## Acceptance Criteria

1. **AC1**: ETW Input Form (`step 2`) submits data to backend and advances workflow
2. **AC2**: Code Review Approval (`step 4`) displays generated PR details and submits approval/rejection
3. **AC3**: Results Confirmation (`step 6`) displays detector results from backend and accepts user confirmation
4. **AC4**: Production Promotion Approval (`step 8`) shows promotion details and handles approval
5. **AC5**: WorkflowStepper component shows real-time step progress based on backend state
6. **AC6**: Each step displays loading state while backend processes executor
7. **AC7**: Step-specific errors are displayed with actionable error messages
8. **AC8**: Completed steps show success indicators; failed steps show error states

## Integration Verification

- **IV1**: Complete entire workflow from step 1-9 and verify each step advances correctly
- **IV2**: Reject approval at step 4 and verify workflow handles rejection gracefully
- **IV3**: Trigger failure at step 3 (schema discovery) and verify error is displayed to user
- **IV4**: Verify WorkflowStepper visual state matches backend workflow state at each step

## Technical Notes

### Workflow Steps

1. **Detector Triage** - Chat interface (Story 6.4)
2. **ETW Input Collection** - Form component
3. **Schema Discovery** - Loading/processing state
4. **Code Generation** - Loading/processing state
5. **PR Creation & Review** - Approval dialog
6. **Deployment Verification** - Loading/processing state
7. **Results Analysis** - Results confirmation dialog
8. **Results Confirmation** - Approval dialog
9. **Production Promotion** - Approval dialog

### Step-Specific Components

- **ETWInputForm**: `client/src/components/workflow/etw-input-form.tsx`
- **ApprovalDialog**: `client/src/components/workflow/approval-dialog.tsx`
- **WorkflowStepper**: `client/src/components/workflow/workflow-stepper.tsx`

### Input Submission Formats

```typescript
// ETW Input (Step 2)
{ input_type: "etw_input", data: { providerGuid: string, ruleId: string } }

// Approval (Steps 4, 6, 8)
{ input_type: "approval", data: { approved: boolean, feedback?: string, reason?: string } }
```

## Dependencies

- **Depends on**: Story 6.1 (Core Frontend Refactoring)
- **Depends on**: Story 6.2 (Backend REST API Integration)
- **Depends on**: Story 6.3 (WebSocket Integration)
- **Depends on**: Story 6.4 (Enhanced Chat Interface)

## Related Documents

- PRD: docs/prd.md (Story 1.5)
- Workflow Components: client/src/components/workflow/
- Backend Workflow: workflows/detector_workflow.py
