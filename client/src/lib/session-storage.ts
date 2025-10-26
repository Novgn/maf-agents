/**
 * Session storage utilities for workflow persistence
 */

import { ChatMessage } from "./types";

export interface StoredWorkflowSession {
  workflowId: string;
  lastUpdated: string;
  currentStep: number;
  status: string;
  chatHistory?: ChatMessage[];
}

const WORKFLOW_STORAGE_PREFIX = "maf-agents-workflow-";
const ACTIVE_WORKFLOWS_KEY = "maf-agents-active-workflows";

/**
 * Save workflow session to localStorage
 */
export function saveWorkflowSession(session: StoredWorkflowSession): void {
  if (typeof window === "undefined") return;

  try {
    const key = `${WORKFLOW_STORAGE_PREFIX}${session.workflowId}`;
    localStorage.setItem(key, JSON.stringify(session));

    // Update active workflows list
    const activeWorkflows = getActiveWorkflows();
    if (!activeWorkflows.includes(session.workflowId)) {
      activeWorkflows.push(session.workflowId);
      localStorage.setItem(ACTIVE_WORKFLOWS_KEY, JSON.stringify(activeWorkflows));
    }
  } catch (error) {
    console.error("Failed to save workflow session:", error);
  }
}

/**
 * Load workflow session from localStorage
 */
export function loadWorkflowSession(workflowId: string): StoredWorkflowSession | null {
  if (typeof window === "undefined") return null;

  try {
    const key = `${WORKFLOW_STORAGE_PREFIX}${workflowId}`;
    const data = localStorage.getItem(key);
    if (!data) return null;

    return JSON.parse(data) as StoredWorkflowSession;
  } catch (error) {
    console.error("Failed to load workflow session:", error);
    return null;
  }
}

/**
 * Remove workflow session from localStorage
 */
export function removeWorkflowSession(workflowId: string): void {
  if (typeof window === "undefined") return;

  try {
    const key = `${WORKFLOW_STORAGE_PREFIX}${workflowId}`;
    localStorage.removeItem(key);

    // Remove from active workflows list
    const activeWorkflows = getActiveWorkflows().filter((id) => id !== workflowId);
    localStorage.setItem(ACTIVE_WORKFLOWS_KEY, JSON.stringify(activeWorkflows));
  } catch (error) {
    console.error("Failed to remove workflow session:", error);
  }
}

/**
 * Get list of active workflow IDs
 */
export function getActiveWorkflows(): string[] {
  if (typeof window === "undefined") return [];

  try {
    const data = localStorage.getItem(ACTIVE_WORKFLOWS_KEY);
    if (!data) return [];

    return JSON.parse(data) as string[];
  } catch (error) {
    console.error("Failed to get active workflows:", error);
    return [];
  }
}

/**
 * Get the most recently updated workflow session
 */
export function getLatestWorkflowSession(): StoredWorkflowSession | null {
  const activeWorkflows = getActiveWorkflows();
  if (activeWorkflows.length === 0) return null;

  let latest: StoredWorkflowSession | null = null;
  let latestTime = 0;

  for (const workflowId of activeWorkflows) {
    const session = loadWorkflowSession(workflowId);
    if (session) {
      const time = new Date(session.lastUpdated).getTime();
      if (time > latestTime) {
        latestTime = time;
        latest = session;
      }
    }
  }

  return latest;
}

/**
 * Clean up old workflow sessions
 * - Completed workflows: remove after 24 hours
 * - Failed workflows: remove after 7 days
 * - Active/running workflows: keep indefinitely
 */
export function cleanupOldSessions(): void {
  if (typeof window === "undefined") return;

  const now = Date.now();
  const oneDayMs = 24 * 60 * 60 * 1000;
  const sevenDaysMs = 7 * oneDayMs;

  const activeWorkflows = getActiveWorkflows();

  for (const workflowId of activeWorkflows) {
    const session = loadWorkflowSession(workflowId);
    if (!session) {
      // Remove invalid session
      removeWorkflowSession(workflowId);
      continue;
    }

    const age = now - new Date(session.lastUpdated).getTime();

    // Clean up completed workflows after 24 hours
    if (session.status === "completed" && age > oneDayMs) {
      console.log(`Cleaning up completed workflow ${workflowId} (${age / oneDayMs} days old)`);
      removeWorkflowSession(workflowId);
      continue;
    }

    // Clean up failed workflows after 7 days
    if (session.status === "failed" && age > sevenDaysMs) {
      console.log(`Cleaning up failed workflow ${workflowId} (${age / oneDayMs} days old)`);
      removeWorkflowSession(workflowId);
      continue;
    }
  }
}
