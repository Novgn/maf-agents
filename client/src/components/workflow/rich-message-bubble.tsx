"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Bot,
  User,
  CheckCircle2,
  AlertCircle,
  Code,
  ArrowRight,
  Loader2,
  ThumbsUp,
  ThumbsDown
} from "lucide-react";
import { ChatMessage, FormField } from "@/lib/types";

interface RichMessageBubbleProps {
  message: ChatMessage;
  onFormSubmit?: (data: Record<string, string>) => void;
  onApproval?: (approved: boolean, feedback?: string) => void;
}

export function RichMessageBubble({ message, onFormSubmit, onApproval }: RichMessageBubbleProps) {
  const { type, content, metadata } = message;

  // Render based on message type
  switch (type) {
    case "user":
      return <UserMessage content={content} />;

    case "agent":
      return <AgentMessage content={content} />;

    case "system":
      return <SystemMessage content={content} />;

    case "step_transition":
      return <StepTransitionMessage content={content} step={metadata?.step} />;

    case "form_request":
      return (
        <FormRequestMessage
          content={content}
          fields={metadata?.formFields || []}
          onSubmit={onFormSubmit}
        />
      );

    case "approval_request":
      return (
        <ApprovalRequestMessage
          content={content}
          approvalData={metadata?.approvalData}
          onApproval={onApproval}
        />
      );

    case "progress":
      return <ProgressMessage content={content} progress={metadata?.progress || 0} />;

    case "artifact":
      return <ArtifactMessage content={content} language={metadata?.language} />;

    case "error":
      return <ErrorMessage content={content} />;

    default:
      // Backwards compatibility: if role is set, render as user or agent
      if (message.role === "user") {
        return <UserMessage content={content} />;
      }
      return <AgentMessage content={content} />;
  }
}

function UserMessage({ content }: { content: string }) {
  return (
    <div className="flex items-start gap-3 flex-row-reverse">
      <div className="rounded-full bg-blue-600 p-2">
        <User className="h-5 w-5 text-white" />
      </div>
      <div className="bg-blue-600 text-white rounded-lg px-4 py-3 max-w-[80%]">
        <p className="text-sm">{content}</p>
      </div>
    </div>
  );
}

function AgentMessage({ content }: { content: string }) {
  return (
    <div className="flex items-start gap-3">
      <div className="rounded-full bg-blue-100 p-2">
        <Bot className="h-5 w-5 text-blue-600" />
      </div>
      <div className="bg-gray-100 rounded-lg px-4 py-3 max-w-[80%]">
        <div className="text-sm prose prose-sm max-w-none">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

function SystemMessage({ content }: { content: string }) {
  return (
    <div className="flex justify-center my-2">
      <div className="bg-gray-200 text-gray-700 rounded-full px-4 py-1.5 text-xs font-medium">
        {content}
      </div>
    </div>
  );
}

function StepTransitionMessage({ content, step }: { content: string; step?: number }) {
  return (
    <div className="flex justify-center my-3">
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="flex items-center gap-2 py-3 px-4">
          <ArrowRight className="h-4 w-4 text-blue-600" />
          <span className="text-sm font-medium text-blue-900">
            {step && `Step ${step}: `}{content}
          </span>
        </CardContent>
      </Card>
    </div>
  );
}

function FormRequestMessage({
  content,
  fields,
  onSubmit
}: {
  content: string;
  fields: FormField[];
  onSubmit?: (data: Record<string, string>) => void;
}) {
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      onSubmit?.(formData);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex items-start gap-3">
      <div className="rounded-full bg-blue-100 p-2">
        <Bot className="h-5 w-5 text-blue-600" />
      </div>
      <Card className="max-w-[80%]">
        <CardContent className="pt-4">
          <div className="text-sm prose prose-sm max-w-none mb-4">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
          <form onSubmit={handleSubmit} className="space-y-3">
            {fields.map((field) => (
              <div key={field.name} className="space-y-1.5">
                <Label htmlFor={field.name} className="text-sm font-medium">
                  {field.label}
                  {field.required && <span className="text-red-500 ml-1">*</span>}
                </Label>
                {field.type === "textarea" ? (
                  <Textarea
                    id={field.name}
                    placeholder={field.placeholder}
                    required={field.required}
                    value={formData[field.name] || ""}
                    onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
                    className="text-sm"
                  />
                ) : field.type === "select" ? (
                  <select
                    id={field.name}
                    required={field.required}
                    value={formData[field.name] || ""}
                    onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option value="">Select...</option>
                    {field.options?.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <Input
                    id={field.name}
                    type={field.type}
                    placeholder={field.placeholder}
                    required={field.required}
                    pattern={field.pattern}
                    value={formData[field.name] || ""}
                    onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
                    className="text-sm"
                  />
                )}
                {field.helpText && (
                  <p className="text-xs text-gray-500">{field.helpText}</p>
                )}
              </div>
            ))}
            <Button type="submit" disabled={isSubmitting} className="w-full">
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Submitting...
                </>
              ) : (
                "Submit"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function ApprovalRequestMessage({
  content,
  approvalData,
  onApproval
}: {
  content: string;
  approvalData?: { content: string; contentLabel: string; allowFeedback?: boolean };
  onApproval?: (approved: boolean, feedback?: string) => void;
}) {
  const [feedback, setFeedback] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const handleApproval = (approved: boolean) => {
    setIsProcessing(true);
    try {
      onApproval?.(approved, feedback || undefined);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex items-start gap-3">
      <div className="rounded-full bg-blue-100 p-2">
        <Bot className="h-5 w-5 text-blue-600" />
      </div>
      <Card className="max-w-[90%]">
        <CardContent className="pt-4 space-y-4">
          <div className="text-sm prose prose-sm max-w-none">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>

          {approvalData && (
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-gray-600 mb-2">
                {approvalData.contentLabel}
              </p>
              <pre className="text-xs bg-white p-3 rounded border overflow-x-auto max-h-64">
                <code>{approvalData.content}</code>
              </pre>
            </div>
          )}

          {approvalData?.allowFeedback && (
            <div className="space-y-1.5">
              <Label htmlFor="feedback" className="text-sm">
                Feedback (optional)
              </Label>
              <Textarea
                id="feedback"
                placeholder="Add any comments or feedback..."
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                className="text-sm"
                rows={2}
              />
            </div>
          )}

          <div className="flex gap-2">
            <Button
              onClick={() => handleApproval(true)}
              disabled={isProcessing}
              className="flex-1 bg-green-600 hover:bg-green-700"
            >
              <ThumbsUp className="h-4 w-4 mr-2" />
              Approve
            </Button>
            <Button
              onClick={() => handleApproval(false)}
              disabled={isProcessing}
              variant="destructive"
              className="flex-1"
            >
              <ThumbsDown className="h-4 w-4 mr-2" />
              Reject
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ProgressMessage({ content, progress }: { content: string; progress: number }) {
  return (
    <div className="flex items-start gap-3">
      <div className="rounded-full bg-blue-100 p-2">
        <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
      </div>
      <div className="bg-gray-100 rounded-lg px-4 py-3 max-w-[80%] min-w-[300px]">
        <p className="text-sm mb-2">{content}</p>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-1 text-right">{Math.round(progress)}%</p>
      </div>
    </div>
  );
}

function ArtifactMessage({ content, language }: { content: string; language?: string }) {
  return (
    <div className="flex items-start gap-3">
      <div className="rounded-full bg-green-100 p-2">
        <Code className="h-5 w-5 text-green-600" />
      </div>
      <Card className="max-w-[90%]">
        <CardContent className="pt-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <p className="text-sm font-medium">Generated Artifact</p>
            {language && (
              <span className="text-xs bg-gray-200 px-2 py-0.5 rounded">
                {language}
              </span>
            )}
          </div>
          <pre className="text-xs bg-gray-900 text-gray-100 p-4 rounded overflow-x-auto max-h-96">
            <code>{content}</code>
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}

function ErrorMessage({ content }: { content: string }) {
  return (
    <div className="flex items-start gap-3">
      <div className="rounded-full bg-red-100 p-2">
        <AlertCircle className="h-5 w-5 text-red-600" />
      </div>
      <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 max-w-[80%]">
        <p className="text-sm text-red-800">{content}</p>
      </div>
    </div>
  );
}
