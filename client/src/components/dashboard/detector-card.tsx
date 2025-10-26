"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, Clock, ExternalLink } from "lucide-react";
import { DeploymentStatus } from "@/lib/types";

interface DetectorCardProps {
  detectorId: string;
  providerGuid: string;
  providerName: string;
  ruleId: string;
  deploymentStatus: DeploymentStatus;
  environment: string;
  lastUpdated: string;
  repoUrl?: string;
  onClick?: () => void;
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}

function getStatusBadge(status: DeploymentStatus) {
  const variants: Record<
    DeploymentStatus,
    { className: string; icon: React.ReactNode; label: string }
  > = {
    deployed: {
      className: "bg-green-100 text-green-700",
      icon: <CheckCircle2 className="h-3 w-3" />,
      label: "Deployed",
    },
    pending: {
      className: "bg-yellow-100 text-yellow-700",
      icon: <Clock className="h-3 w-3" />,
      label: "Pending",
    },
    failed: {
      className: "bg-red-100 text-red-700",
      icon: <XCircle className="h-3 w-3" />,
      label: "Failed",
    },
  };

  const variant = variants[status];

  return (
    <Badge variant="outline" className={`gap-1 ${variant.className}`}>
      {variant.icon}
      {variant.label}
    </Badge>
  );
}

export function DetectorCard({
  providerGuid,
  providerName,
  ruleId,
  deploymentStatus,
  environment,
  lastUpdated,
  repoUrl,
  onClick,
}: DetectorCardProps) {
  return (
    <Card
      className={`${onClick ? "cursor-pointer hover:shadow-lg transition-shadow" : ""}`}
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <CardTitle className="text-lg">{providerName}</CardTitle>
          {getStatusBadge(deploymentStatus)}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <p className="text-xs font-medium text-muted-foreground">Provider GUID</p>
          <p className="text-sm font-mono">{providerGuid}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-muted-foreground">Rule ID</p>
          <p className="text-sm font-medium">{ruleId}</p>
        </div>
        <div className="flex items-center justify-between pt-2">
          <div>
            <p className="text-xs text-muted-foreground">
              {environment} • Updated {formatTimestamp(lastUpdated)}
            </p>
          </div>
          {repoUrl && (
            <Button
              variant="ghost"
              size="sm"
              asChild
              className="gap-1 h-7 px-2"
              onClick={(e) => e.stopPropagation()}
            >
              <a
                href={repoUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink className="h-3 w-3" />
              </a>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
