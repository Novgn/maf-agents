"use client";

import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { WorkflowStep, StepStatus, WorkflowStepperProps } from "@/lib/types";

const STEP_TITLES = [
  "Detector Triage",
  "ETW Input Collection",
  "Schema Discovery",
  "Code Generation",
  "PR Creation",
  "Approval Gate",
  "Deployment Verification",
  "Results Analysis",
  "Production Promotion",
];

const STEP_DESCRIPTIONS = [
  "Understanding requirements",
  "Collecting technical details",
  "Querying Kusto for schema",
  "Generating detector code",
  "Creating pull request",
  "Awaiting human approval",
  "Monitoring deployment",
  "Analyzing effectiveness",
  "Promoting to production",
];

function StepIcon({ status }: { status: StepStatus }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="h-6 w-6 text-green-600" />;
    case "in_progress":
      return <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />;
    case "failed":
      return <XCircle className="h-6 w-6 text-red-600" />;
    default:
      return <Circle className="h-6 w-6 text-gray-300" />;
  }
}

function StepBadge({ status }: { status: StepStatus }) {
  const variants: Record<StepStatus, { label: string; className: string }> = {
    pending: { label: "Pending", className: "bg-gray-100 text-gray-700" },
    in_progress: { label: "In Progress", className: "bg-blue-100 text-blue-700" },
    completed: { label: "Completed", className: "bg-green-100 text-green-700" },
    failed: { label: "Failed", className: "bg-red-100 text-red-700" },
  };

  const variant = variants[status];

  return (
    <Badge variant="outline" className={cn("ml-auto", variant.className)}>
      {variant.label}
    </Badge>
  );
}

export function WorkflowStepper({ steps, currentStep }: WorkflowStepperProps) {
  return (
    <Card className="w-full">
      <CardContent className="p-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold">Detector Development Workflow</h2>
              <p className="text-sm text-muted-foreground">
                Step {currentStep} of {steps.length}
              </p>
            </div>
          </div>

          <div className="space-y-2">
            {steps.map((step) => {
              const isActive = step.number === currentStep;
              const isPast = step.number < currentStep;

              return (
                <div
                  key={step.id}
                  className={cn(
                    "flex items-start gap-4 p-4 rounded-lg border transition-all",
                    isActive && "bg-blue-50 border-blue-200",
                    isPast && "opacity-60",
                    step.status === "failed" && "bg-red-50 border-red-200"
                  )}
                >
                  <div className="flex-shrink-0 mt-1">
                    <StepIcon status={step.status} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-muted-foreground">
                        {step.number}/9
                      </span>
                      <h3 className="font-semibold">{step.title}</h3>
                      <StepBadge status={step.status} />
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {step.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Helper function to create default steps
export function createDefaultSteps(): WorkflowStep[] {
  return STEP_TITLES.map((title, index) => ({
    id: `step-${index + 1}`,
    number: index + 1,
    title,
    description: STEP_DESCRIPTIONS[index],
    status: "pending" as StepStatus,
  }));
}
