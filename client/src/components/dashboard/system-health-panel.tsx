"use client";

import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";

interface SystemHealthPanelProps {
  isConnected: boolean;
  totalWorkflows: number;
  activeWorkflows: number;
  isLoading?: boolean;
}

export function SystemHealthPanel({
  isConnected,
  totalWorkflows,
  activeWorkflows,
  isLoading = false,
}: SystemHealthPanelProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-around">
          <div className="flex items-center gap-2">
            {isConnected ? (
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            ) : (
              <XCircle className="h-5 w-5 text-red-600" />
            )}
            <div>
              <p className="text-sm font-medium">
                {isConnected ? "Connected" : "Disconnected"}
              </p>
              <p className="text-xs text-muted-foreground">Backend Status</p>
            </div>
          </div>

          <div className="h-10 w-px bg-border" />

          <div className="text-center">
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin mx-auto text-muted-foreground" />
            ) : (
              <p className="text-2xl font-bold">{totalWorkflows}</p>
            )}
            <p className="text-xs text-muted-foreground">Total Workflows</p>
          </div>

          <div className="h-10 w-px bg-border" />

          <div className="text-center">
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin mx-auto text-muted-foreground" />
            ) : (
              <p className="text-2xl font-bold text-blue-600">
                {activeWorkflows}
              </p>
            )}
            <p className="text-xs text-muted-foreground">Active Workflows</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
