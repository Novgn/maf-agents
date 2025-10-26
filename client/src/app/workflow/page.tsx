"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useWorkflow } from "@/hooks/use-workflow";
import { ChatInterface } from "@/components/workflow/chat-interface";
import { ChatMessage } from "@/lib/types";
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
      type: "agent",
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

  // Handle WebSocket messages containing chat responses
  useEffect(() => {
    if (!latestMessage || latestMessage === lastProcessedMessageRef.current) return;

    // Handle new chat_message format from backend
    if (latestMessage.type === "chat_message") {
      lastProcessedMessageRef.current = latestMessage;

      const chatMessage: ChatMessage = {
        type: (latestMessage.message_type as ChatMessage["type"]) || "agent",
        content: (latestMessage.message as string) || "",
        timestamp: (latestMessage.timestamp as string) || new Date().toISOString(),
        metadata: (latestMessage.metadata as ChatMessage["metadata"]) || {},
      };

      // Legitimate use case: subscribing to external WebSocket state and updating React state
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setChatMessages((prev) => [...prev, chatMessage]);
      setIsLoadingResponse(false);
      return;
    }

    // Legacy format: agent_message
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
        type: "agent",
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

  const handleSendMessage = async (message: string) => {
    // Add user message to chat
    const userMessage: ChatMessage = {
      type: "user",
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

  const handleFormSubmit = async (data: Record<string, string>) => {
    try {
      console.log("Form submitted:", data);

      // Determine input type based on current step
      // Step 2 = ETW input, but we can also infer from data keys
      if ("providerGuid" in data && "ruleId" in data) {
        await submitInput("etw_input", data);
      } else {
        // Generic form submission
        await submitInput("form_data", data);
      }
    } catch (err) {
      console.error("Failed to submit form:", err);
    }
  };

  const handleApproval = async (approved: boolean, feedback?: string) => {
    try {
      console.log("Approval:", approved, feedback);
      await submitInput("approval", { approved, feedback: feedback || "" });
    } catch (err) {
      console.error("Failed to submit approval:", err);
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

      {/* Main Content - Unified ChatInterface for entire workflow */}
      <ChatInterface
        title={workflowId ? "Detector Development" : "Let's get started"}
        description={
          workflowId
            ? "Follow the workflow steps to create your detector"
            : "Describe what you want to detect and I'll guide you through the process"
        }
        messages={chatMessages}
        onSendMessage={async (message) => {
          // Auto-create workflow on first message if not exists
          if (!workflowId) {
            const newWorkflowId = await createWorkflow();
            if (newWorkflowId) {
              // Add user message to chat
              const userMessage: ChatMessage = {
                type: "user",
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
        placeholder={currentStep === 1 ? "Describe what you want to detect..." : "Type your message..."}
        currentStep={currentStep}
        onFormSubmit={handleFormSubmit}
        onApproval={handleApproval}
      />
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
