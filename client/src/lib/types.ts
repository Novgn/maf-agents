/**
 * Shared TypeScript type definitions for the MAF Agents frontend application.
 * @module lib/types
 */

/**
 * Possible status values for a workflow step.
 */
export type StepStatus = "pending" | "in_progress" | "completed" | "failed";

/**
 * Represents a single step in the detector development workflow.
 */
export interface WorkflowStep {
  /** Unique identifier for the step */
  id: string;
  /** Numeric position of the step (1-9) */
  number: number;
  /** Display title for the step */
  title: string;
  /** Detailed description of what the step does */
  description: string;
  /** Current status of the step */
  status: StepStatus;
}

/**
 * Workflow status response from the backend API.
 */
export interface WorkflowStatus {
  /** Unique workflow identifier */
  workflow_id: string;
  /** Current workflow status (starting, running, completed, failed) */
  status: string;
  /** Name of the current step */
  current_step: string | null;
  /** Numeric position of the current step (1-9) */
  step_number: number | null;
  /** Total number of steps in the workflow */
  total_steps: number;
  /** Additional workflow data */
  data: Record<string, unknown>;
  /** Error message if workflow failed */
  error: string | null;
}

/**
 * Response from creating a new workflow.
 */
export interface WorkflowCreateResponse {
  /** Unique workflow identifier */
  workflow_id: string;
  /** Initial workflow status */
  status: string;
  /** ISO timestamp of workflow creation */
  created_at: string;
}

/**
 * User input payload for submitting data to workflow steps.
 */
export interface UserInput {
  /** Type of input (e.g., "triage_message", "etw_input", "approval") */
  input_type: string;
  /** Input data specific to the input type */
  data: Record<string, unknown>;
}

/**
 * Chat message types for different kinds of workflow events
 */
export type ChatMessageType =
  | "user"              // User text input
  | "agent"             // Agent conversational response
  | "system"            // System status/notification
  | "step_transition"   // Moving to a new workflow step
  | "form_request"      // Request for structured input (inline form)
  | "approval_request"  // Request for approval with actions
  | "progress"          // Progress update with percentage
  | "artifact"          // Generated code/results to display
  | "error";            // Error message

/**
 * Chat message in the conversational interface.
 * Supports rich message types for full E2E workflow visibility.
 */
export interface ChatMessage {
  /** Type of message for rendering */
  type: ChatMessageType;
  /** Message content (supports markdown) */
  content: string;
  /** ISO timestamp of when message was sent */
  timestamp: string;
  /** Optional metadata for the message */
  metadata?: {
    /** Workflow step number when message was sent */
    step?: number;
    /** Message subtype for specialized rendering */
    subtype?: string;
    /** Progress percentage (0-100) for progress messages */
    progress?: number;
    /** Form fields for form_request messages */
    formFields?: FormField[];
    /** Approval options for approval_request messages */
    approvalData?: ApprovalData;
    /** Code language for artifact messages */
    language?: string;
    /** Additional data associated with the message */
    data?: Record<string, unknown>;
  };

  /** @deprecated Use type instead - kept for backwards compatibility */
  role?: "user" | "assistant";
}

/**
 * Form field definition for inline forms in chat
 */
export interface FormField {
  /** Field identifier */
  name: string;
  /** Display label */
  label: string;
  /** Input type */
  type: "text" | "textarea" | "select" | "number";
  /** Placeholder text */
  placeholder?: string;
  /** Whether field is required */
  required?: boolean;
  /** Validation pattern */
  pattern?: string;
  /** Help text */
  helpText?: string;
  /** Options for select fields */
  options?: { value: string; label: string }[];
}

/**
 * Approval request data for inline approvals in chat
 */
export interface ApprovalData {
  /** Content to review (code, results, etc.) */
  content: string;
  /** Label for the content being reviewed */
  contentLabel: string;
  /** Type of approval */
  approvalType: "pr_review" | "results_confirmation" | "production_promotion";
  /** Whether feedback is allowed */
  allowFeedback?: boolean;
}

/**
 * Global workflow context type for React Context provider.
 */
export interface WorkflowContextType {
  /** Current workflow ID, null if no workflow active */
  workflowId: string | null;
  /** Current workflow status */
  status: string | null;
  /** Current step number (0 if not started) */
  currentStep: number;
  /** Array of all workflow steps with their statuses */
  steps: WorkflowStep[];
  /** Error message if workflow encountered an error */
  error: string | null;
  /** WebSocket connection status */
  isConnected: boolean;
  /** Whether WebSocket is attempting to reconnect */
  isReconnecting: boolean;
  /** Whether fallback polling mode is active */
  isUsingPolling: boolean;
  /** Whether a workflow is currently being created */
  isCreatingWorkflow: boolean;
  /** Whether input is currently being submitted */
  isSubmittingInput: boolean;
  /** Latest WebSocket message received */
  latestMessage: Record<string, unknown> | null;
  /** Creates a new workflow session and returns the workflow ID */
  createWorkflow: () => Promise<string | null>;
  /** Submits user input to the current workflow step */
  submitInput: (inputType: string, data: Record<string, unknown>, explicitWorkflowId?: string) => Promise<void>;
}

/**
 * Props for components that accept workflow steps.
 */
export interface WorkflowStepperProps {
  /** Array of workflow steps to display */
  steps: WorkflowStep[];
  /** Current active step number */
  currentStep: number;
}

/**
 * Props for the chat interface component.
 */
export interface ChatInterfaceProps {
  /** Title displayed at the top of the chat */
  title: string;
  /** Optional description text below the title */
  description?: string;
  /** Array of chat messages to display */
  messages: ChatMessage[];
  /** Callback when user sends a message */
  onSendMessage: (message: string) => void;
  /** Whether the chat is waiting for a response */
  isLoading?: boolean;
  /** Placeholder text for the input field */
  placeholder?: string;
  /** Current workflow step number (optional, for phase indicator) */
  currentStep?: number;
  /** Callback when inline form is submitted */
  onFormSubmit?: (data: Record<string, string>) => void;
  /** Callback when approval is given/rejected */
  onApproval?: (approved: boolean, feedback?: string) => void;
}

/**
 * WebSocket message type from backend
 */
export type WebSocketMessageType =
  | "workflow_update"
  | "workflow_complete"
  | "workflow_failed"
  | "step_update";

/**
 * WebSocket message structure from backend
 */
export interface WebSocketMessage {
  /** Type of message */
  type: WebSocketMessageType;
  /** Workflow ID */
  workflow_id: string;
  /** Current workflow status */
  status: string;
  /** Current step number (1-9) */
  step_number?: number;
  /** Name of the current step */
  current_step?: string;
  /** Additional data payload */
  data?: Record<string, unknown>;
  /** Error message if applicable */
  error?: string;
}

/**
 * Detailed information about a single workflow step execution
 */
export interface WorkflowStepDetail {
  /** Step number (1-9) */
  step_number: number;
  /** Display name of the step */
  step_name: string;
  /** Step execution status */
  status: string;
  /** ISO timestamp when step started */
  started_at: string;
  /** ISO timestamp when step completed */
  completed_at: string;
  /** Duration in seconds */
  duration_seconds: number;
  /** Error message if step failed */
  error?: string;
}

/**
 * Generated artifacts from workflow execution
 */
export interface WorkflowArtifacts {
  /** Pull request URL in Azure DevOps */
  pr_url?: string;
  /** Pull request number */
  pr_number?: number;
  /** Generated detector code */
  detector_code?: string;
  /** Results analysis summary */
  results_summary?: string;
}

/**
 * Input data provided by user during workflow
 */
export interface WorkflowInputData {
  /** ETW Provider GUID */
  providerGuid: string;
  /** Detector Rule ID */
  ruleId: string;
}

/**
 * Complete workflow detail for history view
 */
export interface WorkflowDetail {
  /** Unique workflow identifier */
  workflow_id: string;
  /** Final workflow status */
  status: string;
  /** ISO timestamp when workflow was created */
  created_at: string;
  /** ISO timestamp when workflow completed */
  completed_at: string;
  /** Detailed step execution information */
  steps: WorkflowStepDetail[];
  /** Complete chat conversation history */
  chat_history: ChatMessage[];
  /** Generated artifacts and outputs */
  artifacts: WorkflowArtifacts;
  /** User-provided input data */
  input_data: WorkflowInputData;
}

/**
 * Deployment status for a detector
 */
export type DeploymentStatus = "deployed" | "pending" | "failed";

/**
 * Active detector information from backend
 */
export interface Detector {
  /** Unique detector identifier */
  detector_id: string;
  /** ETW Provider GUID */
  provider_guid: string;
  /** Human-readable provider name */
  provider_name: string;
  /** Detector rule ID */
  rule_id: string;
  /** Deployment status */
  deployment_status: DeploymentStatus;
  /** Deployment environment (e.g., production, staging) */
  environment: string;
  /** ISO timestamp when detector was created */
  created_at: string;
  /** ISO timestamp when detector was last updated */
  last_updated: string;
  /** Azure DevOps repository URL */
  repo_url?: string;
}

/**
 * Response from listing detectors API
 */
export interface DetectorListResponse {
  /** Array of active detectors */
  detectors: Detector[];
  /** Total number of detectors */
  total: number;
}
