"""
Unit tests for the Schema Discovery Agent.

Tests query construction, result parsing, and agent functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from agents.schema_discovery_agent import (
    SchemaDiscoveryAgent,
    create_schema_discovery_agent,
    query_existing_detectors,
    query_etw_schema,
    EXISTING_DETECTORS_QUERY_TEMPLATE,
    ETW_SCHEMA_QUERY_TEMPLATE,
)
from shared.kusto_client import KustoClientWrapper
from shared.models import KustoSchemaData, KustoSchemaField


class TestQueryTemplates:
    """Tests for Kusto query templates."""

    def test_existing_detectors_query_template_format(self):
        """Test that existing detectors query template formats correctly."""
        provider_guid = "12345678-1234-1234-1234-123456789012"
        query = EXISTING_DETECTORS_QUERY_TEMPLATE.format(provider_guid=provider_guid)

        assert provider_guid in query
        assert "DetectorTable" in query
        assert "ProviderGuid" in query
        assert "DetectorName" in query

    def test_etw_schema_query_template_format(self):
        """Test that ETW schema query template formats correctly."""
        provider_guid = "12345678-1234-1234-1234-123456789012"
        query = ETW_SCHEMA_QUERY_TEMPLATE.format(provider_guid=provider_guid)

        assert provider_guid in query
        assert "ETWSchemaTable" in query
        assert "FieldName" in query
        assert "DataType" in query


class TestQueryExistingDetectors:
    """Tests for query_existing_detectors tool function."""

    @pytest.mark.asyncio
    async def test_query_existing_detectors_success(self):
        """Test successful query for existing detectors."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)
        mock_kusto_client.execute_query.return_value = [
            {"DetectorName": "Detector1", "RuleId": "rule1"},
            {"DetectorName": "Detector2", "RuleId": "rule2"},
            {"DetectorName": "Detector3", "RuleId": "rule3"},
        ]

        result = await query_existing_detectors(
            provider_guid="12345678-1234-1234-1234-123456789012",
            kusto_client=mock_kusto_client
        )

        assert "Found 3 existing detector(s)" in result
        assert "Detector1" in result
        assert "Detector2" in result
        assert "Detector3" in result

    @pytest.mark.asyncio
    async def test_query_existing_detectors_no_results(self):
        """Test query with no existing detectors found."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)
        mock_kusto_client.execute_query.return_value = []

        result = await query_existing_detectors(
            provider_guid="12345678-1234-1234-1234-123456789012",
            kusto_client=mock_kusto_client
        )

        assert "No existing detectors found" in result

    @pytest.mark.asyncio
    async def test_query_existing_detectors_error_handling(self):
        """Test error handling when query fails."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)
        mock_kusto_client.execute_query.side_effect = Exception("Query failed")

        result = await query_existing_detectors(
            provider_guid="12345678-1234-1234-1234-123456789012",
            kusto_client=mock_kusto_client
        )

        assert "Error querying existing detectors" in result
        assert "Query failed" in result


class TestQueryETWSchema:
    """Tests for query_etw_schema tool function."""

    @pytest.mark.asyncio
    async def test_query_etw_schema_success(self):
        """Test successful query for ETW schema."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)
        mock_kusto_client.execute_query.return_value = [
            {"FieldName": "EventId", "DataType": "int", "Description": "Event ID"},
            {"FieldName": "Timestamp", "DataType": "datetime", "Description": "Timestamp"},
            {"FieldName": "Message", "DataType": "string", "Description": "Message"},
        ]

        result = await query_etw_schema(
            provider_guid="12345678-1234-1234-1234-123456789012",
            kusto_client=mock_kusto_client
        )

        assert "Schema contains 3 field(s)" in result
        assert "EventId" in result
        assert "Timestamp" in result
        assert "Message" in result

    @pytest.mark.asyncio
    async def test_query_etw_schema_many_fields(self):
        """Test query with many schema fields (truncation)."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)
        mock_kusto_client.execute_query.return_value = [
            {"FieldName": f"Field{i}", "DataType": "string", "Description": f"Field {i}"}
            for i in range(10)
        ]

        result = await query_etw_schema(
            provider_guid="12345678-1234-1234-1234-123456789012",
            kusto_client=mock_kusto_client
        )

        assert "Schema contains 10 field(s)" in result
        assert "and 5 more" in result  # Should truncate after 5 fields

    @pytest.mark.asyncio
    async def test_query_etw_schema_no_results(self):
        """Test query with no schema definition found."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)
        mock_kusto_client.execute_query.return_value = []

        result = await query_etw_schema(
            provider_guid="12345678-1234-1234-1234-123456789012",
            kusto_client=mock_kusto_client
        )

        assert "No schema definition found" in result

    @pytest.mark.asyncio
    async def test_query_etw_schema_error_handling(self):
        """Test error handling when schema query fails."""
        mock_kusto_client = Mock(spec=KustoClientWrapper)
        mock_kusto_client.execute_query.side_effect = Exception("Schema query failed")

        result = await query_etw_schema(
            provider_guid="12345678-1234-1234-1234-123456789012",
            kusto_client=mock_kusto_client
        )

        assert "Error querying ETW schema" in result
        assert "Schema query failed" in result


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
