"""
Unit tests for the Schema Discovery Agent.

Tests query construction, result parsing, and agent functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from agents.schema_discovery_agent import (
    SchemaDiscoveryAgent,
    create_schema_discovery_agent,
)
from shared.kusto_client import KustoClientWrapper
from shared.models import KustoSchemaData


class TestSchemaDiscoveryAgent:
    """Tests for SchemaDiscoveryAgent class."""

    @pytest.mark.asyncio
    async def test_agent_initialization_with_openai(self):
        """Test agent initialization with OpenAI client."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)

        with patch("agents.schema_discovery_agent.OpenAIChatClient") as mock_client:
            agent = SchemaDiscoveryAgent(
                kusto_client=mock_kusto_client,
                use_azure=False
            )

            assert agent.kusto_client == mock_kusto_client
            assert agent.use_azure is False
            mock_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_initialization_with_azure(self):
        """Test agent initialization with Azure OpenAI client."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)

        with patch("agents.schema_discovery_agent.AzureOpenAIChatClient") as mock_client:
            agent = SchemaDiscoveryAgent(
                kusto_client=mock_kusto_client,
                use_azure=True
            )

            assert agent.kusto_client == mock_kusto_client
            assert agent.use_azure is True
            mock_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_discover_schema_success(self):
        """Test successful schema discovery."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)
        mock_kusto_client.execute_query.side_effect = [
            # First call: existing detectors
            [
                {"DetectorName": "Detector1", "RuleId": "rule1"},
                {"DetectorName": "Detector2", "RuleId": "rule2"},
            ],
            # Second call: ETW schema
            [
                {"FieldName": "EventId", "DataType": "int", "Description": "Event ID"},
                {"FieldName": "Timestamp", "DataType": "datetime", "Description": "Timestamp"},
            ],
        ]

        with patch("agents.schema_discovery_agent.OpenAIChatClient"):
            agent = SchemaDiscoveryAgent(
                kusto_client=mock_kusto_client,
                use_azure=False
            )

            # Mock the ChatAgent
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value="Mock agent response")
            agent.agent = mock_agent

            # Run schema discovery
            result = await agent.discover_schema(
                provider_guid="12345678-1234-1234-1234-123456789012",
                rule_id="test-rule"
            )

            # Verify result
            assert isinstance(result, KustoSchemaData)
            assert result.provider_guid == "12345678-1234-1234-1234-123456789012"
            assert len(result.existing_detectors) == 2
            assert "Detector1" in result.existing_detectors
            assert "Detector2" in result.existing_detectors
            assert len(result.schema_fields) == 2
            assert result.schema_fields[0].name == "EventId"
            assert result.schema_fields[1].name == "Timestamp"

    @pytest.mark.asyncio
    async def test_discover_schema_no_existing_detectors(self):
        """Test schema discovery with no existing detectors."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)
        mock_kusto_client.execute_query.side_effect = [
            # First call: no existing detectors
            [],
            # Second call: ETW schema
            [
                {"FieldName": "EventId", "DataType": "int", "Description": "Event ID"},
            ],
        ]

        with patch("agents.schema_discovery_agent.OpenAIChatClient"):
            agent = SchemaDiscoveryAgent(
                kusto_client=mock_kusto_client,
                use_azure=False
            )

            # Mock the ChatAgent
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value="Mock agent response")
            agent.agent = mock_agent

            # Run schema discovery
            result = await agent.discover_schema(
                provider_guid="12345678-1234-1234-1234-123456789012",
                rule_id="test-rule"
            )

            # Verify result
            assert isinstance(result, KustoSchemaData)
            assert len(result.existing_detectors) == 0
            assert len(result.schema_fields) == 1

    @pytest.mark.asyncio
    async def test_discover_schema_query_failure(self):
        """Test schema discovery when queries fail."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)
        mock_kusto_client.execute_query.side_effect = Exception("Query failed")

        with patch("agents.schema_discovery_agent.OpenAIChatClient"):
            agent = SchemaDiscoveryAgent(
                kusto_client=mock_kusto_client,
                use_azure=False
            )

            # Mock the ChatAgent
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value="Mock agent response")
            agent.agent = mock_agent

            # Run schema discovery - should handle errors gracefully
            result = await agent.discover_schema(
                provider_guid="12345678-1234-1234-1234-123456789012",
                rule_id="test-rule"
            )

            # Verify result has empty data but doesn't crash
            assert isinstance(result, KustoSchemaData)
            assert len(result.existing_detectors) == 0
            assert len(result.schema_fields) == 0

    @pytest.mark.asyncio
    async def test_discover_schema_partial_failure(self):
        """Test schema discovery when one query succeeds and one fails."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)
        mock_kusto_client.execute_query.side_effect = [
            # First call: existing detectors succeeds
            [{"DetectorName": "Detector1", "RuleId": "rule1"}],
            # Second call: schema query fails
            Exception("Schema query failed"),
        ]

        with patch("agents.schema_discovery_agent.OpenAIChatClient"):
            agent = SchemaDiscoveryAgent(
                kusto_client=mock_kusto_client,
                use_azure=False
            )

            # Mock the ChatAgent
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value="Mock agent response")
            agent.agent = mock_agent

            # Run schema discovery
            result = await agent.discover_schema(
                provider_guid="12345678-1234-1234-1234-123456789012",
                rule_id="test-rule"
            )

            # Verify detectors found but no schema
            assert isinstance(result, KustoSchemaData)
            assert len(result.existing_detectors) == 1
            assert len(result.schema_fields) == 0


class TestCreateSchemaDiscoveryAgent:
    """Tests for the create_schema_discovery_agent factory function."""

    @pytest.mark.asyncio
    async def test_create_schema_discovery_agent_openai(self):
        """Test factory function creates agent with OpenAI client."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)

        with patch("agents.schema_discovery_agent.OpenAIChatClient"):
            agent = await create_schema_discovery_agent(
                kusto_client=mock_kusto_client,
                use_azure=False
            )

            assert isinstance(agent, SchemaDiscoveryAgent)
            assert agent.kusto_client == mock_kusto_client
            assert agent.use_azure is False

    @pytest.mark.asyncio
    async def test_create_schema_discovery_agent_azure(self):
        """Test factory function creates agent with Azure client."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)

        with patch("agents.schema_discovery_agent.AzureOpenAIChatClient"):
            agent = await create_schema_discovery_agent(
                kusto_client=mock_kusto_client,
                use_azure=True
            )

            assert isinstance(agent, SchemaDiscoveryAgent)
            assert agent.kusto_client == mock_kusto_client
            assert agent.use_azure is True
