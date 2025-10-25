"use client";

import { useWorkflow } from "@/hooks/use-workflow";
import { WorkflowStepper } from "@/components/workflow/workflow-stepper";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, CheckCircle2, Loader2, Play } from "lucide-react";

export default function WorkflowPage() {
  const {
    workflowId,
    status,
    currentStep,
    steps,
    error,
    isConnected,
    createWorkflow,
  } = useWorkflow();

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">Detector Development Workflow</h1>
          <p className="text-muted-foreground mt-2">
            Automated ETW detector development using AI agents
          </p>
        </div>

        {!workflowId && (
          <Button onClick={createWorkflow} size="lg" className="gap-2">
            <Play className="h-5 w-5" />
            Start New Workflow
          </Button>
        )}
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <CardTitle className="text-red-900">Error</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      )}

      {workflowId && (
        <Card>
          <CardHeader>
            <CardTitle>Workflow Status</CardTitle>
            <CardDescription>
              Real-time monitoring of your detector development workflow
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Workflow ID</p>
                <p className="font-mono text-sm">{workflowId.slice(0, 8)}...</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <StatusBadge status={status} />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Current Step</p>
                <p className="font-semibold">
                  {currentStep > 0 ? `${currentStep}/9` : "Starting..."}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Connection</p>
                <div className="flex items-center gap-2">
                  {isConnected ? (
                    <>
                      <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                      <span className="text-sm font-medium text-green-700">Connected</span>
                    </>
                  ) : (
                    <>
                      <div className="h-2 w-2 bg-gray-400 rounded-full" />
                      <span className="text-sm font-medium text-gray-600">Disconnected</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {workflowId && <WorkflowStepper steps={steps} currentStep={currentStep} />}

      {!workflowId && (
        <Card>
          <CardHeader>
            <CardTitle>Welcome to MAF Agents</CardTitle>
            <CardDescription>
              Start a new detector development workflow to automate the creation of ETW detectors
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <FeatureCard
                icon={<CheckCircle2 className="h-8 w-8 text-green-600" />}
                title="AI-Powered"
                description="Leverages Azure OpenAI for intelligent code generation and pattern analysis"
              />
              <FeatureCard
                icon={<CheckCircle2 className="h-8 w-8 text-blue-600" />}
                title="Automated"
                description="Handles the entire workflow from requirements to production deployment"
              />
              <FeatureCard
                icon={<CheckCircle2 className="h-8 w-8 text-purple-600" />}
                title="Integrated"
                description="Seamlessly integrates with Azure DevOps, Kusto, and your existing tools"
              />
            </div>

            <div className="pt-4">
              <Button onClick={createWorkflow} size="lg" className="w-full gap-2">
                <Play className="h-5 w-5" />
                Create Your First Detector
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string | null }) {
  if (!status) {
    return <Badge variant="outline">Unknown</Badge>;
  }

  const variants: Record<string, { className: string; icon: React.ReactNode }> = {
    starting: { className: "bg-blue-100 text-blue-700", icon: <Loader2 className="h-3 w-3 animate-spin" /> },
    running: { className: "bg-blue-100 text-blue-700", icon: <Loader2 className="h-3 w-3 animate-spin" /> },
    completed: { className: "bg-green-100 text-green-700", icon: <CheckCircle2 className="h-3 w-3" /> },
    failed: { className: "bg-red-100 text-red-700", icon: <AlertCircle className="h-3 w-3" /> },
  };

  const variant = variants[status] || { className: "bg-gray-100 text-gray-700", icon: null };

  return (
    <Badge variant="outline" className={`${variant.className} gap-1`}>
      {variant.icon}
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center text-center p-4 border rounded-lg">
      <div className="mb-3">{icon}</div>
      <h3 className="font-semibold mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
