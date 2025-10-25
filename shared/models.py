"""
Data models for maf-agents workflow system.

Defines Pydantic models for workflow state, checkpoints, and intermediate results.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ETWInputData(BaseModel):
    """ETW input parameters collected from user."""

    provider_guid: str = Field(..., description="ETW provider GUID")
    rule_id: str = Field(..., description="Rule ID for the detector")


class KustoSchemaField(BaseModel):
    """Schema field definition from Kusto."""

    name: str
    data_type: str
    description: Optional[str] = None


class KustoSchemaData(BaseModel):
    """ETW schema discovered from Kusto."""

    provider_guid: str
    schema_fields: List[KustoSchemaField] = Field(default_factory=list)
    existing_detectors: List[str] = Field(
        default_factory=list, description="List of existing detector names"
    )
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PatternData(BaseModel):
    """Code patterns extracted from historical PRs."""

    naming_patterns: Dict[str, str] = Field(default_factory=dict)
    code_patterns: Dict[str, str] = Field(default_factory=dict)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GeneratedCodeData(BaseModel):
    """Generated detector code files."""

    detector_file_name: str
    detector_code: str
    test_file_name: Optional[str] = None
    test_code: Optional[str] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PRMetadata(BaseModel):
    """Pull request metadata."""

    pr_id: int
    pr_url: str
    branch_name: str
    title: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DeploymentStatus(BaseModel):
    """Deployment verification status."""

    pr_merged: bool = False
    merge_timestamp: Optional[datetime] = None
    deployment_detected: bool = False
    deployment_timestamp: Optional[datetime] = None
    pipeline_status: Optional[str] = None


class ResultsAnalysisData(BaseModel):
    """Detector results analysis."""

    detector_name: str
    events_detected: int = 0
    error_rate: float = 0.0
    analysis_summary: str
    results_acceptable: bool = False
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PromotionData(BaseModel):
    """Production promotion metadata."""

    promotion_pr_id: Optional[int] = None
    promotion_pr_url: Optional[str] = None
    promotion_branch: Optional[str] = None
    promoted_at: Optional[datetime] = None


class ErrorInfo(BaseModel):
    """Error information for failed workflows."""

    error_message: str
    error_type: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    stack_trace: Optional[str] = None


class WorkflowCheckpoint(BaseModel):
    """
    Complete workflow state checkpoint.

    This model represents the full state of a workflow at a specific point in time,
    enabling recovery and resumption after interruptions.
    """

    # Core workflow identification
    workflow_id: str = Field(..., description="Unique workflow identifier (UUID)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Workflow progress tracking
    current_step: str = Field(
        ..., description="Current agent/step in the workflow"
    )
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING)

    # Workflow data (progressively populated)
    etw_input: Optional[ETWInputData] = None
    schema_data: Optional[KustoSchemaData] = None
    pattern_data: Optional[PatternData] = None
    generated_code: Optional[GeneratedCodeData] = None
    pr_metadata: Optional[PRMetadata] = None
    deployment_status: Optional[DeploymentStatus] = None
    results_analysis: Optional[ResultsAnalysisData] = None
    promotion_data: Optional[PromotionData] = None

    # Error tracking
    error_info: Optional[ErrorInfo] = None

    # Metadata
    checkpoint_count: int = Field(
        default=0, description="Number of checkpoints saved for this workflow"
    )
    last_checkpoint_step: Optional[str] = None

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        },
    )
