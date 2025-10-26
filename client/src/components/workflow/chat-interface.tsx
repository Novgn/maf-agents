"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Bot, Send, User, CheckCircle2, Circle } from "lucide-react";
import { ChatMessage, ChatInterfaceProps } from "@/lib/types";

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
                <div className="flex flex-col items-center justify-center h-full text-center py-12">
                  <Bot className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    Start the conversation to begin your detector development
                  </p>
                </div>
              ) : (
                messages.map((message, index) => (
                  <MessageBubble key={index} message={message} />
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

/**
 * Format timestamp to human-readable format
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  // Less than 1 minute ago
  if (diffMins < 1) {
    return "Just now";
  }

  // Less than 1 hour ago
  if (diffMins < 60) {
    return `${diffMins}m ago`;
  }

  // Less than 24 hours ago
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }

  // Less than 7 days ago
  if (diffDays < 7) {
    return `${diffDays}d ago`;
  }

  // More than 7 days ago, show date
  return date.toLocaleDateString();
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex items-start gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`rounded-full p-2 ${isUser ? "bg-blue-600" : "bg-blue-100"}`}>
        {isUser ? (
          <User className={`h-5 w-5 ${isUser ? "text-white" : "text-blue-600"}`} />
        ) : (
          <Bot className="h-5 w-5 text-blue-600" />
        )}
      </div>
      <div
        className={`rounded-lg px-4 py-3 max-w-[80%] ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-900"
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="text-sm prose prose-sm max-w-none prose-p:my-2 prose-headings:my-2 prose-ul:my-2 prose-ol:my-2">
            <ReactMarkdown
              components={{
                // Style markdown elements to match message bubble
                p: ({ children }) => <p className="text-gray-900">{children}</p>,
                strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                em: ({ children }) => <em className="italic text-gray-900">{children}</em>,
                code: ({ children }) => (
                  <code className="bg-gray-200 px-1.5 py-0.5 rounded text-xs font-mono text-gray-900">
                    {children}
                  </code>
                ),
                pre: ({ children }) => (
                  <pre className="bg-gray-200 p-2 rounded overflow-x-auto my-2">
                    {children}
                  </pre>
                ),
                ul: ({ children }) => <ul className="list-disc list-inside space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside space-y-1">{children}</ol>,
                li: ({ children }) => <li className="text-gray-900">{children}</li>,
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
        <p className={`text-xs mt-1 ${isUser ? "text-blue-100" : "text-gray-500"}`}>
          {formatTimestamp(message.timestamp)}
        </p>
      </div>
    </div>
  );
}
