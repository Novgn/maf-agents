"""
Azure Table Storage Session Store for maf-agents.

This module provides production-ready session management using Azure Table Storage,
supporting conversation persistence, workflow state tracking, and user context.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
from dataclasses import dataclass

from azure.data.tables import TableServiceClient, TableClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError


@dataclass
class WorkflowSession:
    """Represents a workflow session with all its state and history."""

    workflow_id: str
    user_id: str
    status: str
    current_step: int
    created_at: str
    updated_at: str
    conversation_history: List[Dict[str, Any]]
    workflow_data: Dict[str, Any]
    metadata: Dict[str, Any]

    def __post_init__(self):
        """Ensure all dict fields are properly initialized."""
        if not isinstance(self.conversation_history, list):
            self.conversation_history = []
        if not isinstance(self.workflow_data, dict):
            self.workflow_data = {}
        if not isinstance(self.metadata, dict):
            self.metadata = {}

    def to_entity(self) -> Dict[str, Any]:
        """Convert to Azure Table Storage entity."""
        return {
            "PartitionKey": self.user_id,
            "RowKey": self.workflow_id,
            "status": self.status,
            "current_step": self.current_step,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            # Store complex data as JSON strings
            "conversation_history": json.dumps(self.conversation_history),
            "workflow_data": json.dumps(self.workflow_data),
            "metadata": json.dumps(self.metadata),
        }

    @classmethod
    def from_entity(cls, entity: Dict[str, Any]) -> "WorkflowSession":
        """Create WorkflowSession from Azure Table Storage entity."""
        return cls(
            workflow_id=entity["RowKey"],
            user_id=entity["PartitionKey"],
            status=entity["status"],
            current_step=entity["current_step"],
            created_at=entity["created_at"],
            updated_at=entity["updated_at"],
            conversation_history=json.loads(entity.get("conversation_history", "[]")),
            workflow_data=json.loads(entity.get("workflow_data", "{}")),
            metadata=json.loads(entity.get("metadata", "{}")),
        )


class AzureTableSessionStore:
    """
    Production-ready session store using Azure Table Storage.

    Features:
    - Automatic authentication with DefaultAzureCredential
    - Conversation history persistence
    - Workflow state tracking
    - User context management
    - Automatic table creation
    """

    def __init__(
        self,
        table_name: str = "WorkflowSessions",
        endpoint: Optional[str] = None,
        credential: Optional[Any] = None,
    ):
        """
        Initialize the session store.

        Args:
            table_name: Name of the Azure Table Storage table
            endpoint: Azure Table Storage endpoint URL (e.g., "https://<account>.table.core.windows.net")
            credential: Azure credential (defaults to DefaultAzureCredential)
        """
        self.table_name = table_name

        # Use provided credential or default to Azure CLI/Managed Identity
        if credential is None:
            credential = DefaultAzureCredential()

        if endpoint is None:
            raise ValueError(
                "endpoint must be provided (e.g., 'https://<account>.table.core.windows.net')"
            )

        # Initialize table service client
        self.service_client = TableServiceClient(
            endpoint=endpoint, credential=credential
        )

        # Get or create table
        self.table_client = self._initialize_table()

    def _initialize_table(self) -> TableClient:
        """Create table if it doesn't exist and return table client."""
        try:
            # Try to create the table
            self.service_client.create_table(self.table_name)
            print(f"✓ Created table '{self.table_name}'")
        except Exception as e:
            # Table might already exist, which is fine
            if "already exists" not in str(e).lower():
                print(f"ℹ️  Table '{self.table_name}' initialization: {e}")

        return self.service_client.get_table_client(self.table_name)

    async def save_session(self, session: WorkflowSession) -> None:
        """
        Save or update a workflow session.

        Args:
            session: WorkflowSession object to save
        """
        session.updated_at = datetime.now(timezone.utc).isoformat()
        entity = session.to_entity()

        try:
            # Upsert (insert or update)
            self.table_client.upsert_entity(entity)
            print(
                f"✓ Saved session: workflow={session.workflow_id[:8]}, user={session.user_id}"
            )
        except Exception as e:
            print(f"❌ Error saving session: {e}")
            raise

    async def get_session(
        self, workflow_id: str, user_id: str
    ) -> Optional[WorkflowSession]:
        """
        Retrieve a workflow session.

        Args:
            workflow_id: Workflow identifier
            user_id: User identifier

        Returns:
            WorkflowSession object or None if not found
        """
        try:
            entity = self.table_client.get_entity(
                partition_key=user_id, row_key=workflow_id
            )
            return WorkflowSession.from_entity(entity)
        except ResourceNotFoundError:
            return None
        except Exception as e:
            print(f"❌ Error retrieving session: {e}")
            raise

    async def list_user_sessions(
        self, user_id: str, limit: int = 100
    ) -> List[WorkflowSession]:
        """
        List all workflow sessions for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return

        Returns:
            List of WorkflowSession objects
        """
        try:
            query = f"PartitionKey eq '{user_id}'"
            entities = self.table_client.query_entities(
                query_filter=query, results_per_page=limit
            )

            sessions = []
            for entity in entities:
                sessions.append(WorkflowSession.from_entity(entity))

            return sorted(sessions, key=lambda s: s.updated_at, reverse=True)
        except Exception as e:
            print(f"❌ Error listing user sessions: {e}")
            raise

    async def delete_session(self, workflow_id: str, user_id: str) -> bool:
        """
        Delete a workflow session.

        Args:
            workflow_id: Workflow identifier
            user_id: User identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            self.table_client.delete_entity(
                partition_key=user_id, row_key=workflow_id
            )
            print(
                f"✓ Deleted session: workflow={workflow_id[:8]}, user={user_id}"
            )
            return True
        except ResourceNotFoundError:
            return False
        except Exception as e:
            print(f"❌ Error deleting session: {e}")
            raise

    async def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Delete sessions older than specified days.

        Args:
            days: Number of days to keep sessions

        Returns:
            Number of sessions deleted
        """
        from datetime import timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()

        deleted_count = 0
        try:
            # Query for old sessions
            query = f"updated_at lt '{cutoff_iso}'"
            entities = self.table_client.query_entities(query_filter=query)

            for entity in entities:
                try:
                    self.table_client.delete_entity(
                        partition_key=entity["PartitionKey"],
                        row_key=entity["RowKey"],
                    )
                    deleted_count += 1
                except Exception as e:
                    print(
                        f"⚠️  Error deleting old session {entity['RowKey']}: {e}"
                    )

            if deleted_count > 0:
                print(
                    f"✓ Cleaned up {deleted_count} sessions older than {days} days"
                )

            return deleted_count
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            raise


# Helper function to create session store from environment variables
def create_session_store_from_env() -> AzureTableSessionStore:
    """
    Create session store using environment variables.

    Required environment variables:
    - AZURE_STORAGE_ENDPOINT: Azure Table Storage endpoint URL

    Optional:
    - AZURE_TABLE_NAME: Table name (defaults to 'WorkflowSessions')

    Uses DefaultAzureCredential for authentication (supports Azure CLI, Managed Identity, etc.)
    """
    import os

    endpoint = os.getenv("AZURE_STORAGE_ENDPOINT")
    if not endpoint:
        raise ValueError(
            "AZURE_STORAGE_ENDPOINT environment variable must be set"
        )

    table_name = os.getenv("AZURE_TABLE_NAME", "WorkflowSessions")

    return AzureTableSessionStore(table_name=table_name, endpoint=endpoint)
