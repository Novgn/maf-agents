"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ArrowRight } from "lucide-react";

interface ETWInputFormProps {
  onSubmit: (data: { providerGuid: string; ruleId: string }) => void;
  isLoading?: boolean;
}

export function ETWInputForm({ onSubmit, isLoading = false }: ETWInputFormProps) {
  const [providerGuid, setProviderGuid] = useState("");
  const [ruleId, setRuleId] = useState("");
  const [errors, setErrors] = useState<{ providerGuid?: string; ruleId?: string }>({});

  const validateGuid = (guid: string): boolean => {
    const guidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return guidRegex.test(guid);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const newErrors: { providerGuid?: string; ruleId?: string } = {};

    if (!providerGuid.trim()) {
      newErrors.providerGuid = "Provider GUID is required";
    } else if (!validateGuid(providerGuid)) {
      newErrors.providerGuid = "Please enter a valid GUID format (e.g., xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)";
    }

    if (!ruleId.trim()) {
      newErrors.ruleId = "Rule ID is required";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    onSubmit({ providerGuid: providerGuid.trim(), ruleId: ruleId.trim() });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>ETW Provider Configuration</CardTitle>
        <CardDescription>
          Enter the ETW provider GUID and rule ID for your detector
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="providerGuid">Provider GUID</Label>
            <Input
              id="providerGuid"
              type="text"
              placeholder="e.g., 12345678-1234-1234-1234-123456789abc"
              value={providerGuid}
              onChange={(e) => {
                setProviderGuid(e.target.value);
                if (errors.providerGuid) {
                  setErrors({ ...errors, providerGuid: undefined });
                }
              }}
              disabled={isLoading}
              className={errors.providerGuid ? "border-red-500" : ""}
            />
            {errors.providerGuid && (
              <p className="text-sm text-red-600">{errors.providerGuid}</p>
            )}
            <p className="text-xs text-muted-foreground">
              The unique identifier for the ETW provider you want to monitor
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="ruleId">Rule ID</Label>
            <Input
              id="ruleId"
              type="text"
              placeholder="e.g., SuspiciousProcessCreation"
              value={ruleId}
              onChange={(e) => {
                setRuleId(e.target.value);
                if (errors.ruleId) {
                  setErrors({ ...errors, ruleId: undefined });
                }
              }}
              disabled={isLoading}
              className={errors.ruleId ? "border-red-500" : ""}
            />
            {errors.ruleId && (
              <p className="text-sm text-red-600">{errors.ruleId}</p>
            )}
            <p className="text-xs text-muted-foreground">
              A descriptive identifier for your detection rule
            </p>
          </div>
        </CardContent>
        <CardFooter>
          <Button type="submit" disabled={isLoading} className="w-full gap-2">
            Continue to Schema Discovery
            <ArrowRight className="h-4 w-4" />
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
