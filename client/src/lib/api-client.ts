/**
 * API client for MAF Agents backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export interface WorkflowStatus {
  workflow_id: string;
  status: string;
  current_step: string | null;
  step_number: number | null;
  total_steps: number;
  data: Record<string, unknown>;
  error: string | null;
}

export interface WorkflowCreateResponse {
  workflow_id: string;
  status: string;
  created_at: string;
}

export interface UserInput {
  input_type: string;
  data: Record<string, unknown>;
}

/**
 * Retry a function with exponential backoff
 * @param fn - The async function to retry
 * @param maxRetries - Maximum number of retry attempts (default: 3)
 * @param baseDelay - Base delay in milliseconds (default: 1000)
 * @returns The result of the function call
 * @throws The last error if all retries fail
 */
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  let lastError: Error | undefined;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      // Don't retry on client errors (4xx)
      if (lastError.message.includes("HTTP 4")) {
        throw lastError;
      }

      // If this was the last retry, throw the error
      if (i === maxRetries - 1) {
        throw lastError;
      }

      // Calculate exponential backoff delay
      const delay = baseDelay * Math.pow(2, i);
      console.warn(
        `API request failed (attempt ${i + 1}/${maxRetries}). Retrying in ${delay}ms...`,
        lastError
      );

      // Wait before retrying
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError || new Error("Max retries exceeded");
}

/**
 * Convert backend error to user-friendly message
 */
function getUserFriendlyErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    // Network errors
    if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
      return "Unable to connect to the server. Please check your internet connection and try again.";
    }

    // Timeout errors
    if (error.message.includes("timeout")) {
      return "The request took too long to complete. Please try again.";
    }

    // HTTP errors
    if (error.message.includes("HTTP 400")) {
      return "Invalid request. Please check your input and try again.";
    }
    if (error.message.includes("HTTP 401")) {
      return "Authentication required. Please log in again.";
    }
    if (error.message.includes("HTTP 403")) {
      return "You don't have permission to perform this action.";
    }
    if (error.message.includes("HTTP 404")) {
      return "The requested resource was not found.";
    }
    if (error.message.includes("HTTP 500")) {
      return "A server error occurred. Please try again later.";
    }
    if (error.message.includes("HTTP 503")) {
      return "The service is temporarily unavailable. Please try again later.";
    }

    // Return the original error message if no specific mapping
    return error.message;
  }

  return "An unexpected error occurred. Please try again.";
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    enableRetry: boolean = true
  ): Promise<T> {
    const makeRequest = async (): Promise<T> => {
      const url = `${this.baseURL}${endpoint}`;
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: response.statusText,
        }));
        const errorMessage = error.detail || `HTTP ${response.status}`;
        throw new Error(errorMessage);
      }

      return response.json();
    };

    try {
      // Use retry logic if enabled (default: true)
      if (enableRetry) {
        return await retryWithBackoff(makeRequest);
      } else {
        return await makeRequest();
      }
    } catch (error) {
      // Convert to user-friendly error message
      const friendlyMessage = getUserFriendlyErrorMessage(error);
      throw new Error(friendlyMessage);
    }
  }

  /**
   * Create a new workflow
   */
  async createWorkflow(
    workflowId?: string
  ): Promise<WorkflowCreateResponse> {
    return this.request<WorkflowCreateResponse>("/api/workflows", {
      method: "POST",
      body: JSON.stringify({ workflow_id: workflowId }),
    });
  }

  /**
   * Get workflow status
   */
  async getWorkflowStatus(workflowId: string): Promise<WorkflowStatus> {
    return this.request<WorkflowStatus>(`/api/workflows/${workflowId}`);
  }

  /**
   * Submit user input to workflow
   */
  async submitInput(workflowId: string, input: UserInput): Promise<void> {
    await this.request(`/api/workflows/${workflowId}/input`, {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  /**
   * List all workflows
   */
  async listWorkflows(): Promise<{
    workflows: Array<{
      workflow_id: string;
      status: string;
      current_step: string;
      created_at: string;
      updated_at: string;
    }>;
    total: number;
  }> {
    return this.request("/api/workflows");
  }

  /**
   * Delete a workflow
   */
  async deleteWorkflow(workflowId: string): Promise<void> {
    await this.request(`/api/workflows/${workflowId}`, {
      method: "DELETE",
    });
  }

  /**
   * Get detailed workflow information (for history/detail view)
   */
  async getWorkflowDetail(workflowId: string): Promise<{
    workflow_id: string;
    status: string;
    created_at: string;
    completed_at: string;
    steps: Array<{
      step_number: number;
      step_name: string;
      status: string;
      started_at: string;
      completed_at: string;
      duration_seconds: number;
      error?: string;
    }>;
    chat_history: Array<{
      role: "user" | "assistant";
      content: string;
      timestamp: string;
    }>;
    artifacts: {
      pr_url?: string;
      pr_number?: number;
      detector_code?: string;
      results_summary?: string;
    };
    input_data: {
      providerGuid: string;
      ruleId: string;
    };
  }> {
    return this.request(`/api/workflows/${workflowId}/detail`);
  }

  /**
   * List all active detectors
   */
  async listDetectors(): Promise<{
    detectors: Array<{
      detector_id: string;
      provider_guid: string;
      provider_name: string;
      rule_id: string;
      deployment_status: "deployed" | "pending" | "failed";
      environment: string;
      created_at: string;
      last_updated: string;
      repo_url?: string;
    }>;
    total: number;
  }> {
    return this.request("/api/detectors");
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string }> {
    return this.request("/health");
  }
}

export const apiClient = new APIClient();

/**
 * WebSocket connection for real-time workflow updates
 */
export function createWorkflowWebSocket(
  workflowId: string,
  callbacks: {
    onMessage?: (data: Record<string, unknown>) => void;
    onError?: (error: Event) => void;
    onClose?: () => void;
    onOpen?: () => void;
  }
): WebSocket {
  const ws = new WebSocket(`${WS_BASE_URL}/ws/workflows/${workflowId}`);

  ws.onopen = () => {
    console.log(`WebSocket connected for workflow: ${workflowId}`);
    callbacks.onOpen?.();
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      callbacks.onMessage?.(data);
    } catch (error) {
      console.error("Failed to parse WebSocket message:", error);
    }
  };

  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
    callbacks.onError?.(error);
  };

  ws.onclose = () => {
    console.log(`WebSocket closed for workflow: ${workflowId}`);
    callbacks.onClose?.();
  };

  return ws;
}
