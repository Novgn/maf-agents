"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Detector } from "@/lib/types";
import { DetectorCard } from "@/components/dashboard/detector-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Plus, Inbox, Search, Shield, Activity, TrendingUp, AlertTriangle } from "lucide-react";

// Placeholder detector data for visualization
const PLACEHOLDER_DETECTORS: Detector[] = [
  {
    detector_id: "det-001",
    provider_guid: "22fb2cd6-0e7c-5a1e-b2c3-0e7c22fb2cd6",
    provider_name: "Microsoft-Windows-Security-Auditing",
    rule_id: "RULE-001",
    deployment_status: "deployed",
    environment: "production",
    created_at: "2025-01-15T10:30:00Z",
    last_updated: "2025-01-20T14:22:00Z",
    repo_url: "https://dev.azure.com/org/project/_git/detectors",
  },
  {
    detector_id: "det-002",
    provider_guid: "3f471139-acb7-4a01-b7a3-6c78ca8b5c41",
    provider_name: "Microsoft-Windows-Kernel-Process",
    rule_id: "RULE-002",
    deployment_status: "deployed",
    environment: "production",
    created_at: "2025-01-18T09:15:00Z",
    last_updated: "2025-01-22T11:10:00Z",
    repo_url: "https://dev.azure.com/org/project/_git/detectors",
  },
  {
    detector_id: "det-003",
    provider_guid: "54849625-5478-4994-a5ba-3e3b0328c30d",
    provider_name: "Microsoft-Windows-PowerShell",
    rule_id: "RULE-003",
    deployment_status: "deployed",
    environment: "production",
    created_at: "2025-01-19T16:45:00Z",
    last_updated: "2025-01-23T08:30:00Z",
    repo_url: "https://dev.azure.com/org/project/_git/detectors",
  },
];

export default function DashboardPage() {
  const router = useRouter();

  // Use placeholder data for now
  const [detectors] = useState<Detector[]>(PLACEHOLDER_DETECTORS);
  const [searchQuery, setSearchQuery] = useState("");

  // Filter detectors by search query
  const filteredDetectors = detectors.filter((detector) => {
    const query = searchQuery.toLowerCase();
    return (
      detector.provider_name.toLowerCase().includes(query) ||
      detector.provider_guid.toLowerCase().includes(query) ||
      detector.rule_id.toLowerCase().includes(query)
    );
  });

  // Placeholder metrics
  const totalDetectors = detectors.length;
  const activeDetectors = detectors.filter((d) => d.deployment_status === "deployed").length;
  const uniqueProviders = new Set(detectors.map((d) => d.provider_name)).size;
  const deploymentSuccessRate = 98.5; // Placeholder percentage

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">ETW Detector Platform</h1>
          <p className="text-muted-foreground mt-2">
            AI-powered detector development and monitoring
          </p>
        </div>
        <Button
          onClick={() => router.push("/workflow")}
          size="lg"
          className="gap-2"
        >
          <Plus className="h-5 w-5" />
          Create New Detector
        </Button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Detectors */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Detectors</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalDetectors}</div>
            <p className="text-xs text-muted-foreground">
              Across all environments
            </p>
          </CardContent>
        </Card>

        {/* Active Detectors */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Detectors</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeDetectors}</div>
            <p className="text-xs text-muted-foreground">
              Currently deployed
            </p>
          </CardContent>
        </Card>

        {/* ETW Providers */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ETW Providers</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{uniqueProviders}</div>
            <p className="text-xs text-muted-foreground">
              Unique providers monitored
            </p>
          </CardContent>
        </Card>

        {/* Success Rate */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{deploymentSuccessRate}%</div>
            <p className="text-xs text-muted-foreground">
              Deployment success
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Active Detectors Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Active Detectors</CardTitle>
              <CardDescription>
                ETW detectors currently deployed and monitored
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by provider name, GUID, or rule ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Detectors Grid */}
          {filteredDetectors.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16">
              <Inbox className="h-16 w-16 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                {searchQuery ? "No detectors found" : "No active detectors"}
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                {searchQuery
                  ? "Try adjusting your search query"
                  : "Create your first detector to get started"}
              </p>
              {!searchQuery && (
                <Button onClick={() => router.push("/workflow")} className="gap-2">
                  <Plus className="h-4 w-4" />
                  Create New Detector
                </Button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredDetectors.map((detector) => (
                <DetectorCard
                  key={detector.detector_id}
                  detectorId={detector.detector_id}
                  providerGuid={detector.provider_guid}
                  providerName={detector.provider_name}
                  ruleId={detector.rule_id}
                  deploymentStatus={detector.deployment_status}
                  environment={detector.environment}
                  lastUpdated={detector.last_updated}
                  repoUrl={detector.repo_url}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
