"""
Checkpoint persistence manager for workflow state management.

Provides checkpoint save/load/list functionality using Azure Table Storage
to enable workflow recovery and resumption after interruptions.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from azure.data.tables import TableServiceClient, TableClient
from azure.core.exceptions import ResourceNotFoundError
import structlog

from shared.models import WorkflowCheckpoint, WorkflowStatus

logger = structlog.get_logger(__name__)


class CheckpointManager:
    """Manages workflow checkpoint persistence to Azure Table Storage."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        table_name: str = "workflowcheckpoints",
    ):
        """
        Initialize the checkpoint manager.

        Args:
            connection_string: Azure Storage connection string
            table_name: Name of the table to store checkpoints (default: workflowcheckpoints)

        Raises:
            ValueError: If connection_string is not provided
        """
        if not connection_string:
            raise ValueError("Azure Storage connection_string is required")

        self.connection_string = connection_string
        self.table_name = table_name

        # Initialize Table Service Client
        self.table_service_client = TableServiceClient.from_connection_string(
            connection_string
        )

        # Create table if it doesn't exist
        try:
            self.table_service_client.create_table(table_name)
            logger.info("Created checkpoint table", table_name=table_name)
        except Exception as e:
            # Table might already exist
            logger.debug(
                "Table creation skipped (may already exist)",
                table_name=table_name,
                error=str(e),
            )

        # Get table client
        self.table_client: TableClient = self.table_service_client.get_table_client(
            table_name
        )
        logger.info("Initialized CheckpointManager", table_name=table_name)

    def save_checkpoint(
        self, workflow_id: str, checkpoint: WorkflowCheckpoint
    ) -> WorkflowCheckpoint:
        """
        Save a workflow checkpoint to Azure Table Storage.

        Args:
            workflow_id: Unique workflow identifier
            checkpoint: WorkflowCheckpoint instance to save

        Returns:
            Updated WorkflowCheckpoint with incremented checkpoint_count

        Raises:
            Exception: If checkpoint save fails
        """
        try:
            # Update checkpoint metadata
            checkpoint.workflow_id = workflow_id
            checkpoint.updated_at = datetime.now(timezone.utc)
            checkpoint.checkpoint_count += 1
            checkpoint.last_checkpoint_step = checkpoint.current_step

            # Convert to dict for storage
            checkpoint_dict = checkpoint.model_dump(mode="json")

            # Prepare entity for Table Storage
            # PartitionKey = workflow_id (for efficient querying by workflow)
            # RowKey = timestamp (for ordering checkpoints chronologically)
            entity = {
                "PartitionKey": workflow_id,
                "RowKey": datetime.now(timezone.utc).isoformat(),
                "checkpoint_data": json.dumps(checkpoint_dict),
                "current_step": checkpoint.current_step,
                "status": checkpoint.status.value if isinstance(checkpoint.status, WorkflowStatus) else checkpoint.status,
                "checkpoint_count": checkpoint.checkpoint_count,
            }

            # Upsert entity (insert or update)
            self.table_client.upsert_entity(entity)

            logger.info(
                "Saved checkpoint",
                workflow_id=workflow_id,
                current_step=checkpoint.current_step,
                checkpoint_count=checkpoint.checkpoint_count,
            )

            return checkpoint

        except Exception as e:
            logger.error(
                "Failed to save checkpoint",
                workflow_id=workflow_id,
                error=str(e),
            )
            raise

    def load_checkpoint(self, workflow_id: str) -> Optional[WorkflowCheckpoint]:
        """
        Load the latest checkpoint for a workflow.

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            WorkflowCheckpoint instance if found, None otherwise

        Raises:
            Exception: If checkpoint load fails (other than not found)
        """
        try:
            # Query for all checkpoints for this workflow, ordered by RowKey (timestamp) descending
            query_filter = f"PartitionKey eq '{workflow_id}'"
            entities = list(
                self.table_client.query_entities(
                    query_filter=query_filter, select=["PartitionKey", "RowKey", "checkpoint_data"]
                )
            )

            if not entities:
                logger.info("No checkpoint found", workflow_id=workflow_id)
                return None

            # Get the latest checkpoint (last in list since RowKey is timestamp)
            latest_entity = sorted(entities, key=lambda x: x["RowKey"], reverse=True)[
                0
            ]

            # Parse checkpoint data
            checkpoint_dict = json.loads(latest_entity["checkpoint_data"])
            checkpoint = WorkflowCheckpoint(**checkpoint_dict)

            logger.info(
                "Loaded checkpoint",
                workflow_id=workflow_id,
                current_step=checkpoint.current_step,
                checkpoint_count=checkpoint.checkpoint_count,
            )

            return checkpoint

        except ResourceNotFoundError:
            logger.info("No checkpoint found", workflow_id=workflow_id)
            return None
        except Exception as e:
            logger.error(
                "Failed to load checkpoint",
                workflow_id=workflow_id,
                error=str(e),
            )
            raise

    def list_checkpoints(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        List all checkpoints for a workflow.

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            List of checkpoint summaries (workflow_id, timestamp, step, status)

        Raises:
            Exception: If checkpoint listing fails
        """
        try:
            query_filter = f"PartitionKey eq '{workflow_id}'"
            entities = list(
                self.table_client.query_entities(
                    query_filter=query_filter,
                    select=["PartitionKey", "RowKey", "current_step", "status", "checkpoint_count"],
                )
            )

            checkpoints = [
                {
                    "workflow_id": entity["PartitionKey"],
                    "timestamp": entity["RowKey"],
                    "current_step": entity.get("current_step"),
                    "status": entity.get("status"),
                    "checkpoint_count": entity.get("checkpoint_count", 0),
                }
                for entity in sorted(entities, key=lambda x: x["RowKey"], reverse=True)
            ]

            logger.info(
                "Listed checkpoints",
                workflow_id=workflow_id,
                count=len(checkpoints),
            )

            return checkpoints

        except Exception as e:
            logger.error(
                "Failed to list checkpoints",
                workflow_id=workflow_id,
                error=str(e),
            )
            raise

    def delete_checkpoint(self, workflow_id: str, timestamp: str) -> bool:
        """
        Delete a specific checkpoint.

        Args:
            workflow_id: Unique workflow identifier
            timestamp: Checkpoint timestamp (RowKey)

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            self.table_client.delete_entity(
                partition_key=workflow_id, row_key=timestamp
            )
            logger.info(
                "Deleted checkpoint",
                workflow_id=workflow_id,
                timestamp=timestamp,
            )
            return True
        except ResourceNotFoundError:
            logger.warning(
                "Checkpoint not found for deletion",
                workflow_id=workflow_id,
                timestamp=timestamp,
            )
            return False
        except Exception as e:
            logger.error(
                "Failed to delete checkpoint",
                workflow_id=workflow_id,
                timestamp=timestamp,
                error=str(e),
            )
            raise

    def delete_all_checkpoints(self, workflow_id: str) -> int:
        """
        Delete all checkpoints for a workflow.

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            Number of checkpoints deleted
        """
        try:
            checkpoints = self.list_checkpoints(workflow_id)
            deleted_count = 0

            for checkpoint in checkpoints:
                if self.delete_checkpoint(workflow_id, checkpoint["timestamp"]):
                    deleted_count += 1

            logger.info(
                "Deleted all checkpoints",
                workflow_id=workflow_id,
                count=deleted_count,
            )

            return deleted_count

        except Exception as e:
            logger.error(
                "Failed to delete all checkpoints",
                workflow_id=workflow_id,
                error=str(e),
            )
            raise


def create_checkpoint_manager(
    connection_string: Optional[str] = None, table_name: str = "workflowcheckpoints"
) -> CheckpointManager:
    """
    Factory function to create a CheckpointManager instance.

    Args:
        connection_string: Azure Storage connection string
        table_name: Name of the table to store checkpoints

    Returns:
        Configured CheckpointManager instance
    """
    return CheckpointManager(
        connection_string=connection_string, table_name=table_name
    )
