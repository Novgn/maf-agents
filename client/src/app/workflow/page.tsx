"use client";

import { useState } from "react";
import { useWorkflow } from "@/hooks/use-workflow";
import { WorkflowStepper } from "@/components/workflow/workflow-stepper";
import { ChatInterface } from "@/components/workflow/chat-interface";
import { ChatMessage } from "@/lib/types";
import { ETWInputForm } from "@/components/workflow/etw-input-form";
import { ApprovalDialog } from "@/components/workflow/approval-dialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { HealthIndicator } from "@/components/HealthIndicator";

export default function WorkflowPage() {
  const {
    workflowId,
    status,
    currentStep,
    steps,
    error,
    isConnected,
    isReconnecting,
    isUsingPolling,
    createWorkflow,
    submitInput,
  } = useWorkflow();

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Hello! I'm here to help you create a new ETW detector. Let's start by understanding what you want to detect. What security event or behavior are you looking to monitor?",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [isLoadingResponse, setIsLoadingResponse] = useState(false);

  // Mock approval data - in real app, this would come from backend
  const [approvalData, setApprovalData] = useState<{
    content: string;
    label: string;
  } | null>(null);

  const handleSendMessage = async (message: string) => {
    // Add user message to chat
    const userMessage: ChatMessage = {
      role: "user",
      content: message,
      timestamp: new Date().toISOString(),
    };
    setChatMessages((prev) => [...prev, userMessage]);
    setIsLoadingResponse(true);

    try {
      // Submit to backend
      await submitInput("triage_message", { message });

      // In a real app, the response would come through WebSocket
      // For now, we'll simulate a response
      setTimeout(() => {
        const assistantMessage: ChatMessage = {
          role: "assistant",
          content: "Thank you for that information. Can you tell me more about the expected behavior and how often you expect this event to occur?",
          timestamp: new Date().toISOString(),
        };
        setChatMessages((prev) => [...prev, assistantMessage]);
        setIsLoadingResponse(false);
      }, 1000);
    } catch (err) {
      setIsLoadingResponse(false);
      console.error("Failed to send message:", err);
    }
  };

  const handleETWSubmit = async (data: { providerGuid: string; ruleId: string }) => {
    try {
      await submitInput("etw_input", data);
    } catch (err) {
      console.error("Failed to submit ETW input:", err);
    }
  };

  const handleApprove = async (feedback?: string) => {
    try {
      await submitInput("approval", { approved: true, feedback });
      setApprovalData(null);
    } catch (err) {
      console.error("Failed to submit approval:", err);
    }
  };

  const handleReject = async (reason: string) => {
    try {
      await submitInput("approval", { approved: false, reason });
      setApprovalData(null);
    } catch (err) {
      console.error("Failed to submit rejection:", err);
    }
  };

  const renderStepContent = () => {
    if (!workflowId) return null;

    switch (currentStep) {
      case 1: // Detector Triage
        return (
          <ChatInterface
            title="Detector Requirements Gathering"
            description="Chat with our AI agent to define your detector requirements"
            messages={chatMessages}
            onSendMessage={handleSendMessage}
            isLoading={isLoadingResponse}
            placeholder="Describe what you want to detect..."
          />
        );

      case 2: // ETW Input Collection
        return (
          <ETWInputForm
            onSubmit={handleETWSubmit}
            isLoading={status === "running"}
          />
        );

      case 4: // Code Review Approval
      case 6: // Results Confirmation
      case 8: // Production Promotion Approval
        if (approvalData) {
          return (
            <ApprovalDialog
              title={
                currentStep === 4
                  ? "Code Review Required"
                  : currentStep === 6
                  ? "Results Confirmation"
                  : "Production Promotion Approval"
              }
              description={
                currentStep === 4
                  ? "Review the generated detector code before proceeding"
                  : currentStep === 6
                  ? "Confirm that the detection results look correct"
                  : "Approve deployment to production"
              }
              content={approvalData.content}
              contentLabel={approvalData.label}
              onApprove={handleApprove}
              onReject={handleReject}
              isLoading={status === "running"}
            />
          );
        }
        return (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="text-muted-foreground">Waiting for approval data...</p>
            </CardContent>
          </Card>
        );

      default:
        // For other steps, just show the stepper
        return (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="text-muted-foreground">Processing step {currentStep}...</p>
              <p className="text-sm text-gray-500 mt-2">
                {steps.find((s) => s.number === currentStep)?.title || "In progress"}
              </p>
            </CardContent>
          </Card>
        );
    }
  };

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Backend Health Check */}
      <HealthIndicator />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">Detector Development Workflow</h1>
          <p className="text-muted-foreground mt-2">
            Automated ETW detector development using AI agents
          </p>
        </div>
      </div>

      {/* Error Display */}
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

      {/* Workflow Status */}
      {workflowId && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Workflow Status</CardTitle>
              <div className="flex items-center gap-2">
                {isConnected ? (
                  <>
                    <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                    <span className="text-sm font-medium text-green-700">Connected</span>
                  </>
                ) : isReconnecting ? (
                  <>
                    <Loader2 className="h-3 w-3 text-yellow-600 animate-spin" />
                    <span className="text-sm font-medium text-yellow-700">Reconnecting...</span>
                  </>
                ) : isUsingPolling ? (
                  <>
                    <div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse" />
                    <span className="text-sm font-medium text-blue-700">Polling Mode</span>
                  </>
                ) : (
                  <>
                    <div className="h-2 w-2 bg-gray-400 rounded-full" />
                    <span className="text-sm font-medium text-gray-600">Disconnected</span>
                  </>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
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
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stepper */}
      {workflowId && <WorkflowStepper steps={steps} currentStep={currentStep} />}

      {/* Step-Specific Content or Default Chat */}
      {workflowId ? (
        renderStepContent()
      ) : (
        <ChatInterface
          title="Start Your Detector Development"
          description="Chat with our AI agent to begin creating a new ETW detector"
          messages={chatMessages}
          onSendMessage={async (message) => {
            // Auto-create workflow on first message if not exists
            if (!workflowId) {
              await createWorkflow();
            }
            await handleSendMessage(message);
          }}
          isLoading={isLoadingResponse}
          placeholder="Tell me what you want to detect..."
        />
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
