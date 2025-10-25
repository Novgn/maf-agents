"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { useState } from "react";

interface ApprovalDialogProps {
  title: string;
  description: string;
  content: string;
  contentLabel?: string;
  onApprove: (feedback?: string) => void;
  onReject: (reason: string) => void;
  isLoading?: boolean;
  allowFeedback?: boolean;
}

export function ApprovalDialog({
  title,
  description,
  content,
  contentLabel = "Generated Content",
  onApprove,
  onReject,
  isLoading = false,
  allowFeedback = true,
}: ApprovalDialogProps) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [showRejectReason, setShowRejectReason] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [rejectReason, setRejectReason] = useState("");

  const handleApprove = () => {
    if (allowFeedback && showFeedback && feedback.trim()) {
      onApprove(feedback.trim());
    } else {
      onApprove();
    }
  };

  const handleReject = () => {
    if (!rejectReason.trim()) {
      setShowRejectReason(true);
      return;
    }
    onReject(rejectReason.trim());
  };

  return (
    <Card className="border-blue-200 bg-blue-50/50">
      <CardHeader>
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-blue-600" />
          <CardTitle className="text-blue-900">{title}</CardTitle>
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-sm font-medium mb-2">{contentLabel}</p>
          <div className="bg-white rounded-lg border p-4 max-h-96 overflow-y-auto">
            <pre className="text-sm whitespace-pre-wrap font-mono">{content}</pre>
          </div>
        </div>

        {allowFeedback && showFeedback && (
          <div>
            <label className="text-sm font-medium mb-2 block">
              Feedback or Changes (Optional)
            </label>
            <Textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Provide any feedback or requested changes..."
              className="min-h-24"
              disabled={isLoading}
            />
          </div>
        )}

        {showRejectReason && (
          <div>
            <label className="text-sm font-medium mb-2 block text-red-700">
              Rejection Reason (Required)
            </label>
            <Textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Please explain why you're rejecting this..."
              className="min-h-24 border-red-300"
              disabled={isLoading}
            />
          </div>
        )}
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button
          onClick={handleApprove}
          disabled={isLoading}
          className="flex-1 gap-2 bg-green-600 hover:bg-green-700"
        >
          <CheckCircle2 className="h-4 w-4" />
          Approve
        </Button>

        {allowFeedback && !showFeedback && !showRejectReason && (
          <Button
            onClick={() => setShowFeedback(true)}
            disabled={isLoading}
            variant="outline"
            className="flex-1"
          >
            Approve with Feedback
          </Button>
        )}

        <Button
          onClick={handleReject}
          disabled={isLoading || (showRejectReason && !rejectReason.trim())}
          variant="destructive"
          className="flex-1 gap-2"
        >
          <XCircle className="h-4 w-4" />
          Reject
        </Button>
      </CardFooter>
    </Card>
  );
}
