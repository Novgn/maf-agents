"use client";

import { Component, ErrorInfo, ReactNode } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, RefreshCw, RotateCw, ExternalLink } from "lucide-react";

/**
 * Props for the ErrorBoundary component.
 */
interface ErrorBoundaryProps {
  /** Child components to wrap with error boundary */
  children: ReactNode;
  /** Optional fallback UI to display when error occurs */
  fallback?: ReactNode;
}

/**
 * State for the ErrorBoundary component.
 */
interface ErrorBoundaryState {
  /** Whether an error has been caught */
  hasError: boolean;
  /** The error that was caught */
  error: Error | null;
  /** Error stack trace for debugging */
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary component that catches React rendering errors.
 * Displays a user-friendly fallback UI when errors occur.
 *
 * @example
 * ```tsx
 * <ErrorBoundary>
 *   <MyComponent />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  /**
   * Static method called when an error is caught.
   * Updates state to trigger fallback UI rendering.
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  /**
   * Lifecycle method called after error is caught.
   * Logs error details for debugging.
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console in development
    console.error("Error caught by boundary:", error, errorInfo);

    // Update state with error details
    this.setState({
      error,
      errorInfo,
    });

    // In production, log to Application Insights or monitoring service
    if (process.env.NODE_ENV === "production") {
      // TODO: Integrate with Application Insights
      // appInsights.trackException({
      //   exception: error,
      //   properties: {
      //     componentStack: errorInfo.componentStack,
      //     userAgent: navigator.userAgent,
      //   }
      // });
      console.error("Production error logged:", error.message);
    }
  }

  /**
   * Resets error boundary state to retry rendering.
   */
  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  /**
   * Reloads the page to attempt recovery.
   */
  handleReload = (): void => {
    window.location.reload();
  };

  /**
   * Opens GitHub issue page with pre-filled error details.
   */
  handleReportIssue = (): void => {
    const { error, errorInfo } = this.state;
    const issueBody = encodeURIComponent(
      `**Error Message:**\n${error?.message || "Unknown error"}\n\n` +
      `**Stack Trace:**\n${error?.stack || "No stack trace"}\n\n` +
      `**Component Stack:**\n${errorInfo?.componentStack || "No component stack"}\n\n` +
      `**Browser:**\n${navigator.userAgent}`
    );
    const issueUrl = `https://github.com/your-org/maf-agents/issues/new?title=UI Error: ${encodeURIComponent(error?.message || "Unknown")}&body=${issueBody}`;
    window.open(issueUrl, "_blank");
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
          <Card className="w-full max-w-2xl border-red-200">
            <CardHeader>
              <div className="flex items-center gap-3">
                <AlertCircle className="h-8 w-8 text-red-600" />
                <div>
                  <CardTitle className="text-red-900">Something went wrong</CardTitle>
                  <CardDescription className="text-red-700">
                    An unexpected error occurred in the application
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {this.state.error && (
                <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                  <p className="font-mono text-sm text-red-900">
                    {this.state.error.message}
                  </p>
                </div>
              )}

              {process.env.NODE_ENV === "development" && this.state.errorInfo && (
                <details className="p-4 bg-gray-100 rounded-lg border">
                  <summary className="cursor-pointer font-medium text-sm text-gray-700 mb-2">
                    Error Details (Development Only)
                  </summary>
                  <pre className="text-xs overflow-auto text-gray-600 whitespace-pre-wrap">
                    {this.state.errorInfo.componentStack}
                  </pre>
                </details>
              )}

              <div className="flex flex-wrap gap-3">
                <Button onClick={this.handleReset} variant="outline" className="gap-2">
                  <RefreshCw className="h-4 w-4" />
                  Try Again
                </Button>
                <Button onClick={this.handleReload} className="gap-2">
                  <RotateCw className="h-4 w-4" />
                  Reload Page
                </Button>
                <Button onClick={this.handleReportIssue} variant="outline" className="gap-2">
                  <ExternalLink className="h-4 w-4" />
                  Report Issue
                </Button>
              </div>

              <p className="text-sm text-gray-600">
                If this problem persists, please{" "}
                <button
                  onClick={this.handleReportIssue}
                  className="underline hover:text-gray-900"
                >
                  report it on GitHub
                </button>
                {" "}or contact support.
              </p>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
