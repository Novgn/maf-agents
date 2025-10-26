"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Bot, Send, CheckCircle2, Circle } from "lucide-react";
import { ChatMessage, ChatInterfaceProps } from "@/lib/types";
import { RichMessageBubble } from "./rich-message-bubble";

const WORKFLOW_PHASES = [
  { number: 1, name: "Triage & Ideation" },
  { number: 2, name: "ETW Input Collection" },
  { number: 3, name: "Schema Discovery" },
  { number: 4, name: "Code Generation" },
  { number: 5, name: "PR Creation" },
  { number: 6, name: "Approval Gate" },
  { number: 7, name: "Deployment" },
  { number: 8, name: "Results Analysis" },
  { number: 9, name: "Production Promotion" },
];

export function ChatInterface({
  title,
  description,
  messages,
  onSendMessage,
  isLoading = false,
  placeholder = "Type your message...",
  currentStep,
  onFormSubmit,
  onApproval,
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput("");
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_240px] gap-4">
      {/* Main Chat Card */}
      <Card className="h-[600px] flex flex-col">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          {description && (
            <p className="text-sm text-muted-foreground">{description}</p>
          )}
        </CardHeader>
        <CardContent className="flex-1 overflow-hidden p-0">
          <ScrollArea className="h-full px-6">
            <div className="space-y-4 py-4">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center py-12 px-4">
                  <Bot className="h-16 w-16 text-blue-500 mb-6" />
                  <h3 className="text-lg font-semibold mb-2">Start Creating Your Detector</h3>
                  <p className="text-muted-foreground mb-6 max-w-md">
                    Describe the security event or behavior you want to detect. I'll help you create an ETW detector automatically.
                  </p>

                  <div className="w-full max-w-2xl space-y-2">
                    <p className="text-xs text-muted-foreground mb-2">Example prompts:</p>
                    <button
                      onClick={() => onSendMessage("Detect suspicious PowerShell execution with encoded commands")}
                      className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors text-sm"
                    >
                      💻 Detect suspicious PowerShell execution with encoded commands
                    </button>
                    <button
                      onClick={() => onSendMessage("Monitor for potential credential dumping activities")}
                      className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors text-sm"
                    >
                      🔐 Monitor for potential credential dumping activities
                    </button>
                    <button
                      onClick={() => onSendMessage("Track unusual network connections from system processes")}
                      className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors text-sm"
                    >
                      🌐 Track unusual network connections from system processes
                    </button>
                    <button
                      onClick={() => onSendMessage("Detect file exfiltration attempts to external storage")}
                      className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors text-sm"
                    >
                      📁 Detect file exfiltration attempts to external storage
                    </button>
                  </div>
                </div>
              ) : (
                messages.map((message, index) => (
                  <RichMessageBubble
                    key={index}
                    message={message}
                    onFormSubmit={onFormSubmit}
                    onApproval={onApproval}
                  />
                ))
              )}
              {isLoading && (
                <div className="flex items-start gap-3">
                  <div className="rounded-full bg-blue-100 p-2">
                    <Bot className="h-5 w-5 text-blue-600" />
                  </div>
                  <div className="bg-gray-100 rounded-lg px-4 py-3 max-w-[80%]">
                    <div className="flex gap-1">
                      <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={scrollRef} />
            </div>
          </ScrollArea>
        </CardContent>
        <CardFooter className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex w-full gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={placeholder}
              disabled={isLoading}
              className="flex-1"
            />
            <Button type="submit" disabled={!input.trim() || isLoading} size="icon">
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </CardFooter>
      </Card>

      {/* Workflow Phases Sidebar - Hidden on mobile, visible on large screens */}
      <Card className="hidden lg:block h-[600px]">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Workflow Phases</CardTitle>
        </CardHeader>
        <CardContent className="p-4 pt-0">
          <div className="space-y-2">
            {WORKFLOW_PHASES.map((phase) => {
              const isCompleted = currentStep ? phase.number < currentStep : false;
              const isCurrent = currentStep === phase.number;

              return (
                <div
                  key={phase.number}
                  className={`flex items-start gap-2 text-xs transition-colors ${
                    isCurrent
                      ? "text-blue-600 font-medium"
                      : isCompleted
                      ? "text-green-600"
                      : "text-muted-foreground"
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  ) : (
                    <Circle
                      className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                        isCurrent ? "fill-blue-600" : ""
                      }`}
                    />
                  )}
                  <div className="flex-1">
                    <div className="leading-tight">{phase.name}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

