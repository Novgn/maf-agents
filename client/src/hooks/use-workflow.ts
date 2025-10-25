"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { apiClient } from "@/lib/api-client";
import { WebSocketManager } from "@/lib/websocket-manager";
import { WorkflowStep, StepStatus, WorkflowContextType } from "@/lib/types";
import { createDefaultSteps } from "@/components/workflow/workflow-stepper";
import {
  saveWorkflowSession,
  getLatestWorkflowSession,
  cleanupOldSessions,
} from "@/lib/session-storage";

/**
 * Custom hook for managing workflow state and WebSocket connections.
 * Handles workflow creation, input submission, and real-time status updates.
 *
 * @returns {WorkflowContextType} Workflow state and control functions
 *
 * @example
 * ```tsx
 * const { workflowId, createWorkflow, submitInput } = useWorkflow();
 *
 * // Create a new workflow
 * await createWorkflow();
 *
 * // Submit user input
 * await submitInput("triage_message", { message: "Hello" });
 * ```
 */
export function useWorkflow(): WorkflowContextType {
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [steps, setSteps] = useState<WorkflowStep[]>(createDefaultSteps());
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isCreatingWorkflow, setIsCreatingWorkflow] = useState(false);
  const [isSubmittingInput, setIsSubmittingInput] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [isUsingPolling, setIsUsingPolling] = useState(false);
  const [latestMessage, setLatestMessage] = useState<Record<string, unknown> | null>(null);

  const wsManagerRef = useRef<WebSocketManager | null>(null);
  const hasRestoredSession = useRef(false);

  // Session restoration on mount
  useEffect(() => {
    if (hasRestoredSession.current) return;

    // Clean up old sessions first
    cleanupOldSessions();

    // Try to restore latest session
    const latestSession = getLatestWorkflowSession();
    if (latestSession) {
      console.log("Restoring workflow session:", latestSession.workflowId);

      // Query backend for latest state
      apiClient
        .getWorkflowStatus(latestSession.workflowId)
        .then((backendState) => {
          // Backend is source of truth
          setWorkflowId(backendState.workflow_id);
          setStatus(backendState.status);
          setCurrentStep(backendState.step_number || 0);

          // Update steps based on backend state
          setSteps((prevSteps) =>
            prevSteps.map((step) => {
              if (backendState.step_number && step.number < backendState.step_number) {
                return { ...step, status: "completed" as StepStatus };
              } else if (step.number === backendState.step_number) {
                return { ...step, status: "in_progress" as StepStatus };
              }
              return step;
            })
          );

          if (backendState.error) {
            setError(backendState.error);
          }
        })
        .catch((err) => {
          console.error("Failed to restore workflow from backend:", err);
          // Still set the workflow ID from localStorage to attempt connection
          setWorkflowId(latestSession.workflowId);
          setCurrentStep(latestSession.currentStep);
          setStatus(latestSession.status);
        });
    }

    hasRestoredSession.current = true;
  }, []);

  // Save session state to localStorage whenever it changes
  useEffect(() => {
    if (!workflowId || !hasRestoredSession.current) return;

    saveWorkflowSession({
      workflowId,
      lastUpdated: new Date().toISOString(),
      currentStep,
      status: status || "starting",
    });
  }, [workflowId, currentStep, status]);

  /**
   * Updates the status of a specific workflow step.
   * @param stepNumber - The step number to update (1-9)
   * @param newStatus - The new status for the step
   */
  const updateStepStatus = useCallback((stepNumber: number, newStatus: StepStatus) => {
    setSteps((prevSteps) =>
      prevSteps.map((step) =>
        step.number === stepNumber ? { ...step, status: newStatus } : step
      )
    );
  }, []);

  /**
   * Handles incoming WebSocket messages and updates workflow state.
   * @param data - WebSocket message data
   */
  const handleWorkflowUpdate = useCallback(
    (data: Record<string, unknown>) => {
      console.log("Workflow update:", data);

      // Store the latest message for components to access
      setLatestMessage(data);

      // Update overall status
      if (data.status && typeof data.status === "string") {
        setStatus(data.status);
      }

      // Update current step
      if (data.step_number && typeof data.step_number === "number") {
        setCurrentStep(data.step_number);

        // Mark previous steps as completed
        for (let i = 1; i < data.step_number; i++) {
          updateStepStatus(i, "completed");
        }

        // Mark current step as in progress
        updateStepStatus(data.step_number, "in_progress");
      }

      // Handle specific event types
      if (data.type === "workflow_complete") {
        updateStepStatus(9, "completed");
      } else if (data.type === "workflow_failed") {
        const errorMessage =
          typeof data.error === "string" ? data.error : "Workflow failed";
        setError(errorMessage);
        if (data.step_number && typeof data.step_number === "number") {
          updateStepStatus(data.step_number, "failed");
        }
      }
    },
    [updateStepStatus]
  );

  /**
   * Creates a new workflow session.
   * Clears any previous errors and initializes workflow state.
   */
  const createWorkflow = useCallback(async () => {
    setIsCreatingWorkflow(true);
    try {
      setError(null);
      const response = await apiClient.createWorkflow();
      setWorkflowId(response.workflow_id);
      setStatus(response.status);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create workflow");
    } finally {
      setIsCreatingWorkflow(false);
    }
  }, []);

  /**
   * Submits user input to the current workflow step.
   * @param inputType - Type of input (e.g., "triage_message", "etw_input", "approval")
   * @param data - Input data payload
   */
  const submitInput = useCallback(async (inputType: string, data: Record<string, unknown>) => {
    if (!workflowId) {
      setError("No workflow ID");
      return;
    }

    setIsSubmittingInput(true);
    try {
      await apiClient.submitInput(workflowId, { input_type: inputType, data });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit input");
    } finally {
      setIsSubmittingInput(false);
    }
  }, [workflowId]);

  // WebSocket connection management with reconnection and polling fallback
  useEffect(() => {
    if (!workflowId) return;

    // Create WebSocket manager with automatic reconnection
    const wsManager = new WebSocketManager(
      workflowId,
      {
        onOpen: () => {
          setIsConnected(true);
          setIsReconnecting(false);
          setIsUsingPolling(false);
          console.log("Connected to workflow WebSocket");
        },
        onMessage: handleWorkflowUpdate,
        onError: (error) => {
          console.error("WebSocket error:", error);
        },
        onClose: () => {
          setIsConnected(false);
          console.log("Disconnected from workflow WebSocket");
        },
        onReconnecting: (attempt) => {
          setIsReconnecting(true);
          setIsConnected(false);
          console.log(`Reconnecting... (attempt ${attempt})`);
        },
        onFallbackToPolling: () => {
          setIsUsingPolling(true);
          setIsReconnecting(false);
          setIsConnected(false);
          console.log("Fell back to polling mode");
        },
      },
      {
        maxReconnectAttempts: 3,
        initialReconnectDelay: 1000,
        maxReconnectDelay: 30000,
        pollingInterval: 5000,
      }
    );

    wsManagerRef.current = wsManager;

    // Cleanup on unmount
    return () => {
      if (wsManagerRef.current) {
        wsManagerRef.current.close();
        wsManagerRef.current = null;
      }
    };
  }, [workflowId, handleWorkflowUpdate]);

  return {
    workflowId,
    status,
    currentStep,
    steps,
    error,
    isConnected,
    isReconnecting,
    isUsingPolling,
    isCreatingWorkflow,
    isSubmittingInput,
    latestMessage,
    createWorkflow,
    submitInput,
  };
}
