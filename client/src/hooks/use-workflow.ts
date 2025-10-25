"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { apiClient, createWorkflowWebSocket, WorkflowStatus } from "@/lib/api-client";
import { WorkflowStep, createDefaultSteps, StepStatus } from "@/components/workflow/workflow-stepper";

interface UseWorkflowResult {
  workflowId: string | null;
  status: string | null;
  currentStep: number;
  steps: WorkflowStep[];
  error: string | null;
  isConnected: boolean;
  createWorkflow: () => Promise<void>;
  submitInput: (inputType: string, data: Record<string, any>) => Promise<void>;
}

export function useWorkflow(): UseWorkflowResult {
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [steps, setSteps] = useState<WorkflowStep[]>(createDefaultSteps());
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);

  const updateStepStatus = useCallback((stepNumber: number, newStatus: StepStatus) => {
    setSteps((prevSteps) =>
      prevSteps.map((step) =>
        step.number === stepNumber ? { ...step, status: newStatus } : step
      )
    );
  }, []);

  const handleWorkflowUpdate = useCallback((data: any) => {
    console.log("Workflow update:", data);

    // Update overall status
    if (data.status) {
      setStatus(data.status);
    }

    // Update current step
    if (data.step_number) {
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
      setError(data.error || "Workflow failed");
      if (data.step_number) {
        updateStepStatus(data.step_number, "failed");
      }
    }
  }, [updateStepStatus]);

  const createWorkflow = useCallback(async () => {
    try {
      setError(null);
      const response = await apiClient.createWorkflow();
      setWorkflowId(response.workflow_id);
      setStatus(response.status);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create workflow");
    }
  }, []);

  const submitInput = useCallback(async (inputType: string, data: Record<string, any>) => {
    if (!workflowId) {
      setError("No workflow ID");
      return;
    }

    try {
      await apiClient.submitInput(workflowId, { input_type: inputType, data });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit input");
    }
  }, [workflowId]);

  // WebSocket connection management
  useEffect(() => {
    if (!workflowId) return;

    // Create WebSocket connection
    const ws = createWorkflowWebSocket(workflowId, {
      onOpen: () => {
        setIsConnected(true);
        console.log("Connected to workflow WebSocket");
      },
      onMessage: handleWorkflowUpdate,
      onError: (error) => {
        console.error("WebSocket error:", error);
        setIsConnected(false);
      },
      onClose: () => {
        setIsConnected(false);
        console.log("Disconnected from workflow WebSocket");
      },
    });

    wsRef.current = ws;

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
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
    createWorkflow,
    submitInput,
  };
}
