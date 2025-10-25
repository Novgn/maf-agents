"""
Unit tests for the checkpoint persistence module.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from shared.checkpoint import CheckpointManager, create_checkpoint_manager
from shared.models import (
    WorkflowCheckpoint,
    WorkflowStatus,
    ETWInputData,
    KustoSchemaData,
    KustoSchemaField,
)


@pytest.fixture
def mock_table_service():
    """Fixture for mocked TableServiceClient."""
    with patch("shared.checkpoint.TableServiceClient") as mock_service:
        mock_client = Mock()
        mock_service.from_connection_string.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_table_client():
    """Fixture for mocked TableClient."""
    mock_client = Mock()
    return mock_client


@pytest.fixture
def checkpoint_manager(mock_table_service, mock_table_client):
    """Fixture for CheckpointManager with mocked dependencies."""
    mock_table_service.get_table_client.return_value = mock_table_client
    manager = CheckpointManager(
        connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test123==",
        table_name="testcheckpoints",
    )
    manager.table_client = mock_table_client
    return manager


@pytest.fixture
def sample_checkpoint():
    """Fixture for a sample WorkflowCheckpoint."""
    return WorkflowCheckpoint(
        workflow_id=str(uuid4()),
        current_step="etw_input_collection",
        status=WorkflowStatus.IN_PROGRESS,
        etw_input=ETWInputData(
            provider_guid="12345678-1234-1234-1234-123456789012", rule_id="test-rule-1"
        ),
    )


class TestCheckpointManager:
    """Tests for CheckpointManager class."""

    def test_init_success(self, mock_table_service):
        """Test successful initialization."""
        manager = CheckpointManager(
            connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test123==",
            table_name="testcheckpoints",
        )
        assert manager.table_name == "testcheckpoints"
        assert manager.connection_string is not None

    def test_init_no_connection_string(self):
        """Test initialization fails without connection string."""
        with pytest.raises(ValueError, match="connection_string is required"):
            CheckpointManager(connection_string=None)

    def test_save_checkpoint_success(
        self, checkpoint_manager, mock_table_client, sample_checkpoint
    ):
        """Test successful checkpoint save."""
        workflow_id = str(uuid4())

        result = checkpoint_manager.save_checkpoint(workflow_id, sample_checkpoint)

        # Verify checkpoint was updated
        assert result.workflow_id == workflow_id
        assert result.checkpoint_count == 1
        assert result.last_checkpoint_step == "etw_input_collection"

        # Verify table client was called
        mock_table_client.upsert_entity.assert_called_once()
        call_args = mock_table_client.upsert_entity.call_args[0][0]
        assert call_args["PartitionKey"] == workflow_id
        assert call_args["current_step"] == "etw_input_collection"
        assert call_args["status"] == "in_progress"

    def test_load_checkpoint_success(
        self, checkpoint_manager, mock_table_client, sample_checkpoint
    ):
        """Test successful checkpoint load."""
        workflow_id = str(uuid4())

        # Mock query response
        checkpoint_dict = sample_checkpoint.model_dump(mode="json")
        mock_entity = {
            "PartitionKey": workflow_id,
            "RowKey": datetime.utcnow().isoformat(),
            "checkpoint_data": json.dumps(checkpoint_dict),
        }
        mock_table_client.query_entities.return_value = [mock_entity]

        result = checkpoint_manager.load_checkpoint(workflow_id)

        assert result is not None
        assert result.current_step == sample_checkpoint.current_step
        assert result.etw_input.provider_guid == sample_checkpoint.etw_input.provider_guid

    def test_load_checkpoint_not_found(self, checkpoint_manager, mock_table_client):
        """Test load when no checkpoint exists."""
        workflow_id = str(uuid4())
        mock_table_client.query_entities.return_value = []

        result = checkpoint_manager.load_checkpoint(workflow_id)

        assert result is None

    def test_load_checkpoint_multiple_returns_latest(
        self, checkpoint_manager, mock_table_client, sample_checkpoint
    ):
        """Test load returns the latest checkpoint when multiple exist."""
        workflow_id = str(uuid4())

        # Create two checkpoints with different timestamps
        checkpoint_dict = sample_checkpoint.model_dump(mode="json")
        older_entity = {
            "PartitionKey": workflow_id,
            "RowKey": "2024-01-01T10:00:00",
            "checkpoint_data": json.dumps(checkpoint_dict),
        }

        sample_checkpoint.current_step = "schema_discovery"
        newer_checkpoint_dict = sample_checkpoint.model_dump(mode="json")
        newer_entity = {
            "PartitionKey": workflow_id,
            "RowKey": "2024-01-01T11:00:00",
            "checkpoint_data": json.dumps(newer_checkpoint_dict),
        }

        mock_table_client.query_entities.return_value = [older_entity, newer_entity]

        result = checkpoint_manager.load_checkpoint(workflow_id)

        assert result is not None
        assert result.current_step == "schema_discovery"

    def test_list_checkpoints_success(self, checkpoint_manager, mock_table_client):
        """Test successful checkpoint listing."""
        workflow_id = str(uuid4())

        mock_entities = [
            {
                "PartitionKey": workflow_id,
                "RowKey": "2024-01-01T10:00:00",
                "current_step": "etw_input_collection",
                "status": "in_progress",
                "checkpoint_count": 1,
            },
            {
                "PartitionKey": workflow_id,
                "RowKey": "2024-01-01T11:00:00",
                "current_step": "schema_discovery",
                "status": "in_progress",
                "checkpoint_count": 2,
            },
        ]
        mock_table_client.query_entities.return_value = mock_entities

        result = checkpoint_manager.list_checkpoints(workflow_id)

        assert len(result) == 2
        assert result[0]["workflow_id"] == workflow_id
        assert result[0]["timestamp"] == "2024-01-01T11:00:00"  # Newer first
        assert result[1]["timestamp"] == "2024-01-01T10:00:00"

    def test_list_checkpoints_empty(self, checkpoint_manager, mock_table_client):
        """Test listing when no checkpoints exist."""
        workflow_id = str(uuid4())
        mock_table_client.query_entities.return_value = []

        result = checkpoint_manager.list_checkpoints(workflow_id)

        assert result == []

    def test_delete_checkpoint_success(self, checkpoint_manager, mock_table_client):
        """Test successful checkpoint deletion."""
        workflow_id = str(uuid4())
        timestamp = "2024-01-01T10:00:00"

        result = checkpoint_manager.delete_checkpoint(workflow_id, timestamp)

        assert result is True
        mock_table_client.delete_entity.assert_called_once_with(
            partition_key=workflow_id, row_key=timestamp
        )

    def test_delete_all_checkpoints_success(
        self, checkpoint_manager, mock_table_client
    ):
        """Test successful deletion of all checkpoints."""
        workflow_id = str(uuid4())

        # Mock list_checkpoints to return 2 checkpoints
        checkpoints = [
            {"workflow_id": workflow_id, "timestamp": "2024-01-01T10:00:00"},
            {"workflow_id": workflow_id, "timestamp": "2024-01-01T11:00:00"},
        ]

        with patch.object(
            checkpoint_manager, "list_checkpoints", return_value=checkpoints
        ):
            with patch.object(
                checkpoint_manager, "delete_checkpoint", return_value=True
            ) as mock_delete:
                result = checkpoint_manager.delete_all_checkpoints(workflow_id)

                assert result == 2
                assert mock_delete.call_count == 2


class TestCreateCheckpointManager:
    """Tests for create_checkpoint_manager factory function."""

    def test_factory_function(self, mock_table_service):
        """Test factory function creates CheckpointManager."""
        manager = create_checkpoint_manager(
            connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test123==",
            table_name="testcheckpoints",
        )
        assert isinstance(manager, CheckpointManager)
        assert manager.table_name == "testcheckpoints"


class TestWorkflowCheckpointModel:
    """Tests for WorkflowCheckpoint Pydantic model."""

    def test_minimal_checkpoint_creation(self):
        """Test creating checkpoint with minimal required fields."""
        checkpoint = WorkflowCheckpoint(
            workflow_id="test-workflow-1",
            current_step="etw_input_collection",
            status=WorkflowStatus.IN_PROGRESS,
        )
        assert checkpoint.workflow_id == "test-workflow-1"
        assert checkpoint.current_step == "etw_input_collection"
        assert checkpoint.status == WorkflowStatus.IN_PROGRESS
        assert checkpoint.etw_input is None

    def test_full_checkpoint_creation(self):
        """Test creating checkpoint with all fields populated."""
        checkpoint = WorkflowCheckpoint(
            workflow_id="test-workflow-1",
            current_step="schema_discovery",
            status=WorkflowStatus.IN_PROGRESS,
            etw_input=ETWInputData(
                provider_guid="12345678-1234-1234-1234-123456789012",
                rule_id="test-rule-1",
            ),
            schema_data=KustoSchemaData(
                provider_guid="12345678-1234-1234-1234-123456789012",
                schema_fields=[
                    KustoSchemaField(
                        name="EventId", data_type="int", description="Event identifier"
                    )
                ],
                existing_detectors=["detector1", "detector2"],
            ),
        )
        assert checkpoint.etw_input is not None
        assert checkpoint.schema_data is not None
        assert len(checkpoint.schema_data.schema_fields) == 1
        assert len(checkpoint.schema_data.existing_detectors) == 2

    def test_checkpoint_serialization(self):
        """Test checkpoint can be serialized to JSON."""
        checkpoint = WorkflowCheckpoint(
            workflow_id="test-workflow-1",
            current_step="etw_input_collection",
            status=WorkflowStatus.IN_PROGRESS,
            etw_input=ETWInputData(
                provider_guid="12345678-1234-1234-1234-123456789012",
                rule_id="test-rule-1",
            ),
        )

        # Serialize to dict
        checkpoint_dict = checkpoint.model_dump(mode="json")
        assert isinstance(checkpoint_dict, dict)
        assert checkpoint_dict["workflow_id"] == "test-workflow-1"
        assert checkpoint_dict["status"] == "in_progress"

        # Deserialize back
        restored = WorkflowCheckpoint(**checkpoint_dict)
        assert restored.workflow_id == checkpoint.workflow_id
        assert restored.current_step == checkpoint.current_step
