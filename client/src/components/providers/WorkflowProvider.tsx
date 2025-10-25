"use client";

import React, { createContext, useContext } from "react";
import { WorkflowContextType } from "@/lib/types";
import { useWorkflow } from "@/hooks/use-workflow";

/**
 * React Context for sharing workflow state across the application.
 * Provides workflow ID, status, steps, and control functions.
 */
const WorkflowContext = createContext<WorkflowContextType | undefined>(undefined);

/**
 * Props for the WorkflowProvider component.
 */
interface WorkflowProviderProps {
  /** Child components that will have access to workflow context */
  children: React.ReactNode;
}

/**
 * Provider component that wraps the application and provides workflow state.
 *
 * @param {WorkflowProviderProps} props - Provider props
 * @returns {React.ReactElement} Provider component
 *
 * @example
 * ```tsx
 * <WorkflowProvider>
 *   <App />
 * </WorkflowProvider>
 * ```
 */
export function WorkflowProvider({ children }: WorkflowProviderProps): React.ReactElement {
  const workflowState = useWorkflow();

  return (
    <WorkflowContext.Provider value={workflowState}>
      {children}
    </WorkflowContext.Provider>
  );
}

/**
 * Hook to access workflow context from any component.
 * Must be used within a WorkflowProvider.
 *
 * @returns {WorkflowContextType} Current workflow state and functions
 * @throws {Error} If used outside of WorkflowProvider
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { workflowId, createWorkflow } = useWorkflowContext();
 *
 *   const handleStart = async () => {
 *     await createWorkflow();
 *   };
 *
 *   return <button onClick={handleStart}>Start Workflow</button>;
 * }
 * ```
 */
export function useWorkflowContext(): WorkflowContextType {
  const context = useContext(WorkflowContext);

  if (context === undefined) {
    throw new Error("useWorkflowContext must be used within a WorkflowProvider");
  }

  return context;
}
