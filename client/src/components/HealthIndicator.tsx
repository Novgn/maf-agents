/**
 * Health indicator component
 * Displays the backend connection status
 */

"use client";

import { useHealthCheck } from "@/hooks/use-health-check";
import { AlertCircle, Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function HealthIndicator(): React.ReactElement | null {
  const { isHealthy, isChecking, error, retry } = useHealthCheck();

  // Don't show anything if healthy
  if (isHealthy && !error) {
    return null;
  }

  // Show loading state
  if (isChecking) {
    return (
      <Card className="mb-4 border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
            <div>
              <p className="font-semibold text-blue-900">Connecting to Backend</p>
              <p className="text-sm text-blue-700">Checking backend connectivity...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Show error state
  if (error) {
    return (
      <Card className="mb-4 border-red-200 bg-red-50">
        <CardContent className="pt-6">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <p className="font-semibold text-red-900">Backend Connection Error</p>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={retry}
              className="shrink-0"
            >
              <RefreshCw className="h-3 w-3 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return null;
}
