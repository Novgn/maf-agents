/**
 * Custom hook for backend health check
 */

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api-client";

export interface HealthCheckState {
  /** Whether the backend is healthy and reachable */
  isHealthy: boolean;
  /** Whether the health check is currently loading */
  isChecking: boolean;
  /** Error message if health check failed */
  error: string | null;
  /** Retry the health check manually */
  retry: () => Promise<void>;
}

/**
 * Hook to check backend health on mount and provide retry functionality
 */
export function useHealthCheck(): HealthCheckState {
  const [isHealthy, setIsHealthy] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    setIsChecking(true);
    setError(null);

    try {
      const result = await apiClient.healthCheck();
      if (result.status === "healthy" || result.status === "ok") {
        setIsHealthy(true);
        setError(null);
      } else {
        setIsHealthy(false);
        setError("Backend is not healthy");
      }
    } catch (err) {
      setIsHealthy(false);
      const errorMessage =
        err instanceof Error ? err.message : "Failed to connect to backend";
      setError(errorMessage);
      console.error("Health check failed:", err);
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return {
    isHealthy,
    isChecking,
    error,
    retry: checkHealth,
  };
}
