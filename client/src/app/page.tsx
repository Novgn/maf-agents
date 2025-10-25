"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  CheckCircle2,
  Clock,
  TrendingUp,
  Zap,
  ArrowRight,
  Play,
  AlertCircle
} from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface WorkflowSummary {
  workflow_id: string;
  status: string;
  current_step: string;
  created_at: string;
  updated_at: string;
}

export default function DashboardPage() {
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchWorkflows() {
      try {
        const data = await apiClient.listWorkflows();
        setWorkflows(data.workflows);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch workflows");
      } finally {
        setLoading(false);
      }
    }

    fetchWorkflows();
  }, []);

  const stats = {
    total: workflows.length,
    running: workflows.filter(w => w.status === "running").length,
    completed: workflows.filter(w => w.status === "completed").length,
    failed: workflows.filter(w => w.status === "failed").length,
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto py-8 space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-4 py-8">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            MAF Agents Dashboard
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            AI-powered ETW detector development with automated workflows
          </p>
          <div className="flex gap-4 justify-center pt-4">
            <Link href="/workflow">
              <Button size="lg" className="gap-2">
                <Play className="h-5 w-5" />
                Start New Workflow
              </Button>
            </Link>
            <Button size="lg" variant="outline" asChild>
              <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
                API Documentation
              </a>
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            title="Total Workflows"
            value={stats.total}
            icon={<Activity className="h-8 w-8 text-blue-600" />}
            color="blue"
          />
          <StatCard
            title="Running"
            value={stats.running}
            icon={<Zap className="h-8 w-8 text-yellow-600" />}
            color="yellow"
          />
          <StatCard
            title="Completed"
            value={stats.completed}
            icon={<CheckCircle2 className="h-8 w-8 text-green-600" />}
            color="green"
          />
          <StatCard
            title="Failed"
            value={stats.failed}
            icon={<AlertCircle className="h-8 w-8 text-red-600" />}
            color="red"
          />
        </div>

        {/* Features Section */}
        <Card>
          <CardHeader>
            <CardTitle>Platform Features</CardTitle>
            <CardDescription>
              Comprehensive detector development automation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <FeatureCard
                icon={<TrendingUp className="h-10 w-10 text-blue-600" />}
                title="9-Step Workflow"
                description="Automated pipeline from requirements to production"
                items={[
                  "Detector Triage",
                  "Schema Discovery",
                  "Code Generation",
                  "PR Creation & Approval",
                  "Deployment & Analysis"
                ]}
              />
              <FeatureCard
                icon={<Zap className="h-10 w-10 text-purple-600" />}
                title="AI-Powered"
                description="Azure OpenAI integration for intelligent automation"
                items={[
                  "Conversational agents",
                  "Pattern analysis",
                  "Code generation",
                  "Requirements gathering"
                ]}
              />
              <FeatureCard
                icon={<Clock className="h-10 w-10 text-green-600" />}
                title="Real-time Monitoring"
                description="Live workflow progress and WebSocket updates"
                items={[
                  "Step-by-step tracking",
                  "Checkpoint recovery",
                  "Error handling",
                  "Status notifications"
                ]}
              />
            </div>
          </CardContent>
        </Card>

        {/* Recent Workflows */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Workflows</CardTitle>
                <CardDescription>
                  Latest detector development workflows
                </CardDescription>
              </div>
              <Link href="/workflow">
                <Button variant="outline" size="sm" className="gap-2">
                  View All
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-muted-foreground">
                Loading workflows...
              </div>
            ) : error ? (
              <div className="text-center py-8 text-red-600">
                {error}
              </div>
            ) : workflows.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">No workflows yet</p>
                <Link href="/workflow">
                  <Button>Create Your First Workflow</Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {workflows.slice(0, 5).map((workflow) => (
                  <WorkflowRow key={workflow.workflow_id} workflow={workflow} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Integration Status */}
        <Card>
          <CardHeader>
            <CardTitle>Azure Integrations</CardTitle>
            <CardDescription>Connected services and endpoints</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <IntegrationStatus
                name="Azure OpenAI"
                status="connected"
                description="LLM-powered agents and code generation"
              />
              <IntegrationStatus
                name="Azure Kusto"
                status="connected"
                description="Schema discovery and results analysis"
              />
              <IntegrationStatus
                name="Azure DevOps"
                status="connected"
                description="PR creation and repository management"
              />
              <IntegrationStatus
                name="FastAPI Backend"
                status="connected"
                description="REST and WebSocket API server"
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color }: {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
}) {
  const colorClasses = {
    blue: "border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950",
    yellow: "border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950",
    green: "border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950",
    red: "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950",
  };

  return (
    <Card className={colorClasses[color as keyof typeof colorClasses]}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-3xl font-bold mt-2">{value}</p>
          </div>
          {icon}
        </div>
      </CardContent>
    </Card>
  );
}

function FeatureCard({ icon, title, description, items }: {
  icon: React.ReactNode;
  title: string;
  description: string;
  items: string[];
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-start gap-3">
        {icon}
        <div>
          <h3 className="font-semibold text-lg">{title}</h3>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
      <ul className="space-y-1 ml-12">
        {items.map((item, i) => (
          <li key={i} className="text-sm text-muted-foreground flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full bg-primary" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function WorkflowRow({ workflow }: { workflow: WorkflowSummary }) {
  return (
    <Link href={`/workflow?id=${workflow.workflow_id}`}>
      <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent transition-colors cursor-pointer">
        <div className="flex items-center gap-4">
          <div>
            <p className="font-mono text-sm font-medium">
              {workflow.workflow_id.slice(0, 8)}...
            </p>
            <p className="text-sm text-muted-foreground">
              {workflow.current_step || "Initializing"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <StatusBadge status={workflow.status} />
          <p className="text-sm text-muted-foreground">
            {new Date(workflow.created_at).toLocaleDateString()}
          </p>
        </div>
      </div>
    </Link>
  );
}

function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, { className: string; label: string }> = {
    starting: { className: "bg-blue-100 text-blue-700", label: "Starting" },
    running: { className: "bg-blue-100 text-blue-700", label: "Running" },
    completed: { className: "bg-green-100 text-green-700", label: "Completed" },
    failed: { className: "bg-red-100 text-red-700", label: "Failed" },
  };

  const variant = variants[status] || { className: "bg-gray-100 text-gray-700", label: status };

  return (
    <Badge variant="outline" className={variant.className}>
      {variant.label}
    </Badge>
  );
}

function IntegrationStatus({ name, status, description }: {
  name: string;
  status: string;
  description: string;
}) {
  return (
    <div className="flex items-start gap-3 p-4 border rounded-lg">
      <div className={`h-3 w-3 rounded-full mt-1 ${
        status === "connected" ? "bg-green-500 animate-pulse" : "bg-gray-400"
      }`} />
      <div>
        <p className="font-medium">{name}</p>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
