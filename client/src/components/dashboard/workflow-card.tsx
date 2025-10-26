"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Loader2, XCircle, Clock } from "lucide-react";

interface WorkflowCardProps {
  workflowId: string;
  status: string;
  currentStep: string | null;
  stepNumber: number | null;
  totalSteps: number;
  lastUpdated: string;
  onClick: () => void;
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;

  return date.toLocaleDateString();
}

function getStatusBadge(status: string) {
  const variants: Record<
    string,
    { className: string; icon: React.ReactNode; label: string }
  > = {
    starting: {
      className: "bg-blue-100 text-blue-700",
      icon: <Loader2 className="h-3 w-3 animate-spin" />,
      label: "Starting",
    },
    running: {
      className: "bg-blue-100 text-blue-700",
      icon: <Loader2 className="h-3 w-3 animate-spin" />,
      label: "Running",
    },
    completed: {
      className: "bg-green-100 text-green-700",
      icon: <CheckCircle2 className="h-3 w-3" />,
      label: "Completed",
    },
    failed: {
      className: "bg-red-100 text-red-700",
      icon: <XCircle className="h-3 w-3" />,
      label: "Failed",
    },
  };

  const variant = variants[status] || {
    className: "bg-gray-100 text-gray-700",
    icon: <Clock className="h-3 w-3" />,
    label: status,
  };

  return (
    <Badge variant="outline" className={`gap-1 ${variant.className}`}>
      {variant.icon}
      {variant.label}
    </Badge>
  );
}

export function WorkflowCard({
  workflowId,
  status,
  currentStep,
  stepNumber,
  totalSteps,
  lastUpdated,
  onClick,
}: WorkflowCardProps) {
  return (
    <Card
      className="cursor-pointer hover:shadow-lg transition-shadow"
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-mono">
            {workflowId.slice(0, 8)}...
          </CardTitle>
          {getStatusBadge(status)}
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div>
          <p className="text-sm text-muted-foreground">Current Step</p>
          <p className="text-sm font-medium">
            {stepNumber && totalSteps
              ? `Step ${stepNumber}/${totalSteps}`
              : "Initializing"}
          </p>
          {currentStep && (
            <p className="text-xs text-muted-foreground mt-0.5">
              {currentStep}
            </p>
          )}
        </div>
        <div>
          <p className="text-xs text-muted-foreground">
            Updated {formatTimestamp(lastUpdated)}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
