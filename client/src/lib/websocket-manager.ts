/**
 * WebSocket Manager with automatic reconnection and polling fallback
 */

import { apiClient } from "./api-client";

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

interface WebSocketManagerCallbacks {
  onMessage?: (data: Record<string, unknown>) => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
  onOpen?: () => void;
  onReconnecting?: (attempt: number) => void;
  onFallbackToPolling?: () => void;
}

interface WebSocketManagerOptions {
  /** Maximum number of reconnection attempts before falling back to polling */
  maxReconnectAttempts?: number;
  /** Initial reconnection delay in milliseconds */
  initialReconnectDelay?: number;
  /** Maximum reconnection delay in milliseconds */
  maxReconnectDelay?: number;
  /** Polling interval in milliseconds when WebSocket fails */
  pollingInterval?: number;
}

/**
 * Enhanced WebSocket manager with automatic reconnection and polling fallback
 */
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private workflowId: string;
  private callbacks: WebSocketManagerCallbacks;
  private options: Required<WebSocketManagerOptions>;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pollingTimer: NodeJS.Timeout | null = null;
  private isPolling = false;
  private isClosed = false;

  constructor(
    workflowId: string,
    callbacks: WebSocketManagerCallbacks,
    options: WebSocketManagerOptions = {}
  ) {
    this.workflowId = workflowId;
    this.callbacks = callbacks;
    this.options = {
      maxReconnectAttempts: options.maxReconnectAttempts ?? 3,
      initialReconnectDelay: options.initialReconnectDelay ?? 1000,
      maxReconnectDelay: options.maxReconnectDelay ?? 30000,
      pollingInterval: options.pollingInterval ?? 5000,
    };

    this.connect();
  }

  /**
   * Establish WebSocket connection
   */
  private connect(): void {
    if (this.isClosed) return;

    try {
      const url = `${WS_BASE_URL}/ws/workflows/${this.workflowId}`;
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log(`WebSocket connected for workflow: ${this.workflowId}`);
        this.reconnectAttempts = 0;
        this.stopPolling();
        this.callbacks.onOpen?.();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as Record<string, unknown>;
          this.callbacks.onMessage?.(data);
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
          console.error("Raw message:", event.data);
        }
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.callbacks.onError?.(error);
      };

      this.ws.onclose = () => {
        console.log(`WebSocket closed for workflow: ${this.workflowId}`);
        this.callbacks.onClose?.();

        if (!this.isClosed) {
          this.handleReconnection();
        }
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      this.handleReconnection();
    }
  }

  /**
   * Handle reconnection with exponential backoff
   */
  private handleReconnection(): void {
    if (this.isClosed) return;

    // If we've exceeded max attempts, fall back to polling
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.warn(
        `Max reconnection attempts (${this.options.maxReconnectAttempts}) exceeded. Falling back to polling.`
      );
      this.startPolling();
      return;
    }

    // Calculate exponential backoff delay
    const delay = Math.min(
      this.options.initialReconnectDelay * Math.pow(2, this.reconnectAttempts),
      this.options.maxReconnectDelay
    );

    this.reconnectAttempts++;
    console.log(
      `Reconnection attempt ${this.reconnectAttempts}/${this.options.maxReconnectAttempts} in ${delay}ms...`
    );
    this.callbacks.onReconnecting?.(this.reconnectAttempts);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Start polling workflow status as fallback
   */
  private startPolling(): void {
    if (this.isPolling || this.isClosed) return;

    console.log(
      `Starting polling fallback (interval: ${this.options.pollingInterval}ms)`
    );
    this.isPolling = true;
    this.callbacks.onFallbackToPolling?.();

    const poll = async () => {
      if (this.isClosed || !this.isPolling) return;

      try {
        const status = await apiClient.getWorkflowStatus(this.workflowId);
        // Convert workflow status to WebSocket message format
        const data: Record<string, unknown> = {
          type: "workflow_update",
          workflow_id: status.workflow_id,
          status: status.status,
          step_number: status.step_number,
          current_step: status.current_step,
          data: status.data,
          error: status.error,
        };
        this.callbacks.onMessage?.(data);
      } catch (error) {
        console.error("Polling error:", error);
      }
    };

    // Initial poll
    poll();

    // Set up interval
    this.pollingTimer = setInterval(poll, this.options.pollingInterval);
  }

  /**
   * Stop polling
   */
  private stopPolling(): void {
    if (this.pollingTimer) {
      clearInterval(this.pollingTimer);
      this.pollingTimer = null;
    }
    this.isPolling = false;
  }

  /**
   * Check if currently connected via WebSocket
   */
  public isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Check if using polling fallback
   */
  public isUsingPolling(): boolean {
    return this.isPolling;
  }

  /**
   * Close WebSocket and cleanup
   */
  public close(): void {
    this.isClosed = true;

    // Clear reconnection timer
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    // Stop polling
    this.stopPolling();

    // Close WebSocket
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    console.log(`WebSocket manager closed for workflow: ${this.workflowId}`);
  }
}
