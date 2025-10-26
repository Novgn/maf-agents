"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useWorkflow } from "@/hooks/use-workflow";
import { ChatInterface } from "@/components/workflow/chat-interface";
import { ChatMessage } from "@/lib/types";
import { ETWInputForm } from "@/components/workflow/etw-input-form";
import { ApprovalDialog } from "@/components/workflow/approval-dialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, Loader2 } from "lucide-react";
import { loadWorkflowSession, saveWorkflowSession } from "@/lib/session-storage";

function WorkflowPageContent() {
  const searchParams = useSearchParams();
  const queryWorkflowId = searchParams?.get("id");

  // Pass query parameter to useWorkflow hook to load specific workflow
  const {
    workflowId,
    currentStep,
    steps,
    error,
    latestMessage,
    createWorkflow,
    submitInput,
  } = useWorkflow(queryWorkflowId);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Hello! I'm here to help you create a new ETW detector. Let's start by understanding what you want to detect. What security event or behavior are you looking to monitor?",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [isLoadingResponse, setIsLoadingResponse] = useState(false);
  const [hasChatRestored, setHasChatRestored] = useState(false);

  // Track the last processed message to prevent duplicates
  const lastProcessedMessageRef = useRef<Record<string, unknown> | null>(null);

  // Restore chat history from session storage when workflow is restored
  useEffect(() => {
    if (workflowId && !hasChatRestored) {
      const session = loadWorkflowSession(workflowId);
      if (session?.chatHistory && session.chatHistory.length > 0) {
        console.log("Restoring chat history:", session.chatHistory.length, "messages");
        // Legitimate use case: restoring persisted state from localStorage
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setChatMessages(session.chatHistory);
      }
      setHasChatRestored(true);
    }
  }, [workflowId, hasChatRestored]);

  // Save chat history to session storage whenever it changes
  useEffect(() => {
    if (workflowId && hasChatRestored && chatMessages.length > 0) {
      const session = loadWorkflowSession(workflowId);
      if (session) {
        saveWorkflowSession({
          ...session,
          chatHistory: chatMessages,
          lastUpdated: new Date().toISOString(),
        });
      }
    }
  }, [workflowId, chatMessages, hasChatRestored]);

  // Handle WebSocket messages containing agent chat responses
  useEffect(() => {
    if (!latestMessage || latestMessage === lastProcessedMessageRef.current) return;

    // Check if message contains agent chat response
    // The backend might send: { type: "agent_message", message: "...", ... }
    // or { data: { message: "..." }, ... }
    const messageContent =
      (latestMessage.message && typeof latestMessage.message === "string"
        ? latestMessage.message
        : null) ||
      (latestMessage.data &&
      typeof latestMessage.data === "object" &&
      latestMessage.data !== null &&
      "message" in latestMessage.data &&
      typeof (latestMessage.data as Record<string, unknown>).message === "string"
        ? (latestMessage.data as Record<string, unknown>).message
        : null);

    if (messageContent) {
      // Mark this message as processed
      lastProcessedMessageRef.current = latestMessage;

      // Add agent response to chat
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: messageContent as string,
        timestamp: new Date().toISOString(),
        metadata: {
          step: currentStep,
          data: latestMessage.data as Record<string, unknown> | undefined,
        },
      };
      // Legitimate use case: subscribing to external WebSocket state and updating React state
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setChatMessages((prev) => [...prev, assistantMessage]);
      setIsLoadingResponse(false);
    }
  }, [latestMessage, currentStep]);

  // Approval data from backend WebSocket
  const [approvalData, setApprovalData] = useState<{
    content: string;
    label: string;
  } | null>(null);

  // Handle WebSocket messages for approval steps
  useEffect(() => {
    if (!latestMessage) return;

    // Check for approval_required messages from backend
    if (latestMessage.type === "approval_required" && latestMessage.data) {
      const data = latestMessage.data as Record<string, unknown>;
      const content = data.content && typeof data.content === "string" ? data.content : "";
      const label =
        data.label && typeof data.label === "string"
          ? data.label
          : currentStep === 5
          ? "Generated Pull Request"
          : currentStep === 7
          ? "Detection Results"
          : "Content for Review";

      // Legitimate use case: subscribing to external WebSocket state and updating React state
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setApprovalData({ content, label });
    }
  }, [latestMessage, currentStep]);

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
      // Submit to backend - response will come via WebSocket
      await submitInput("triage_message", { message });

      // Note: The agent response will arrive via WebSocket and be handled by the useEffect above
      // If no response arrives within a reasonable time, we'll timeout the loading state
      setTimeout(() => {
        setIsLoadingResponse(false);
      }, 30000); // 30 second timeout
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

    const currentStepInfo = steps.find((s) => s.number === currentStep);
    const stepStatus = currentStepInfo?.status || "pending";

    // If current step has failed, show error
    if (stepStatus === "failed" && error) {
      return (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <CardTitle className="text-red-900">Step Failed</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-red-800 mb-4">{error}</p>
            <p className="text-sm text-red-700">
              Step {currentStep}: {currentStepInfo?.title}
            </p>
          </CardContent>
        </Card>
      );
    }

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
            currentStep={currentStep}
          />
        );

      case 2: // ETW Input Collection
        return (
          <ETWInputForm
            onSubmit={handleETWSubmit}
            isLoading={stepStatus === "in_progress"}
          />
        );

      case 3: // Schema Discovery (Processing)
        return (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="font-semibold text-lg">Discovering Schema</p>
              <p className="text-muted-foreground mt-2">
                Querying Kusto for ETW event schema...
              </p>
            </CardContent>
          </Card>
        );

      case 4: // Code Generation (Processing)
        return (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="font-semibold text-lg">Generating Detector Code</p>
              <p className="text-muted-foreground mt-2">
                AI is generating detector implementation...
              </p>
            </CardContent>
          </Card>
        );

      case 5: // PR Creation & Review (Approval)
        if (approvalData) {
          return (
            <ApprovalDialog
              title="Code Review Required"
              description="Review the generated detector code and pull request before proceeding"
              content={approvalData.content}
              contentLabel={approvalData.label}
              onApprove={handleApprove}
              onReject={handleReject}
              isLoading={stepStatus === "in_progress"}
            />
          );
        }
        return (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="text-muted-foreground">Creating pull request...</p>
            </CardContent>
          </Card>
        );

      case 6: // Deployment Verification (Processing)
        return (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="font-semibold text-lg">Verifying Deployment</p>
              <p className="text-muted-foreground mt-2">
                Monitoring deployment and initial execution...
              </p>
            </CardContent>
          </Card>
        );

      case 7: // Results Analysis (Approval)
        if (approvalData) {
          return (
            <ApprovalDialog
              title="Detection Results Confirmation"
              description="Review the detection results and confirm they look correct"
              content={approvalData.content}
              contentLabel={approvalData.label}
              onApprove={handleApprove}
              onReject={handleReject}
              isLoading={stepStatus === "in_progress"}
            />
          );
        }
        return (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="text-muted-foreground">Analyzing detection results...</p>
            </CardContent>
          </Card>
        );

      case 8: // Results Confirmation (Processing - in the new numbering this is actually step 8)
        return (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="font-semibold text-lg">Preparing Final Report</p>
              <p className="text-muted-foreground mt-2">
                Compiling deployment summary and metrics...
              </p>
            </CardContent>
          </Card>
        );

      case 9: // Production Promotion (Approval)
        if (approvalData) {
          return (
            <ApprovalDialog
              title="Production Promotion Approval"
              description="Review the deployment summary and approve promotion to production"
              content={approvalData.content}
              contentLabel={approvalData.label}
              onApprove={handleApprove}
              onReject={handleReject}
              isLoading={stepStatus === "in_progress"}
              allowFeedback={false}
            />
          );
        }
        return (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="text-muted-foreground">Preparing promotion details...</p>
            </CardContent>
          </Card>
        );

      default:
        // Fallback for any unexpected step
        return (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="text-muted-foreground">Processing step {currentStep}...</p>
              <p className="text-sm text-gray-500 mt-2">
                {currentStepInfo?.title || "In progress"}
              </p>
            </CardContent>
          </Card>
        );
    }
  };

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header - Simple and clean */}
      <div>
        <h1 className="text-3xl font-bold">Create New Detector</h1>
        <p className="text-muted-foreground mt-1">
          Chat with our AI agent to automatically generate an ETW detector
        </p>
      </div>

      {/* Error Display - Inline and subtle */}
      {error && (
        <div className="flex items-center gap-2 p-4 rounded-lg border border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Main Content - Always show chat interface for smooth flow */}
      {workflowId && currentStep > 0 ? (
        renderStepContent()
      ) : (
        <ChatInterface
          title="Let's get started"
          description="Describe what you want to detect and I'll guide you through the process"
          messages={chatMessages}
          onSendMessage={async (message) => {
            // Auto-create workflow on first message if not exists
            if (!workflowId) {
              const newWorkflowId = await createWorkflow();
              if (newWorkflowId) {
                // Add user message to chat
                const userMessage: ChatMessage = {
                  role: "user",
                  content: message,
                  timestamp: new Date().toISOString(),
                };
                setChatMessages((prev) => [...prev, userMessage]);
                setIsLoadingResponse(true);

                try {
                  // Submit to backend using the just-created workflow ID
                  await submitInput("triage_message", { message }, newWorkflowId);
                  setTimeout(() => {
                    setIsLoadingResponse(false);
                  }, 30000);
                } catch (err) {
                  setIsLoadingResponse(false);
                  console.error("Failed to send message:", err);
                }
              }
            } else {
              // Workflow already exists, use normal flow
              await handleSendMessage(message);
            }
          }}
          isLoading={isLoadingResponse}
          placeholder="Tell me what you want to detect..."
          currentStep={currentStep}
        />
      )}
    </div>
  );
}

export default function WorkflowPage() {
  return (
    <Suspense fallback={
      <div className="container mx-auto py-8 flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    }>
      <WorkflowPageContent />
    </Suspense>
  );
}
