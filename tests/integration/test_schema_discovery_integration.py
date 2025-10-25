"""
Integration tests for Schema Discovery Agent.

Tests complete schema discovery workflow with real Kusto cluster.
Tests are skipped if required environment variables are not set.
"""

import pytest
import os

from agents.schema_discovery_agent import create_schema_discovery_agent
from shared.kusto_client import create_kusto_client
from shared.auth import get_auth_manager
from shared.models import KustoSchemaData


# Check if Kusto integration tests should run
KUSTO_CLUSTER_URL = os.getenv("KUSTO_CLUSTER_URL")
KUSTO_DATABASE_NAME = os.getenv("KUSTO_DATABASE_NAME")
SKIP_KUSTO_INTEGRATION = not (KUSTO_CLUSTER_URL and KUSTO_DATABASE_NAME)
SKIP_REASON = "Kusto integration tests require KUSTO_CLUSTER_URL and KUSTO_DATABASE_NAME environment variables"


@pytest.mark.skipif(SKIP_KUSTO_INTEGRATION, reason=SKIP_REASON)
class TestSchemaDiscoveryIntegration:
    """Integration tests for Schema Discovery Agent against real cluster."""

    @pytest.fixture
    def kusto_client(self):
        """Create a Kusto client for integration testing."""
        assert KUSTO_CLUSTER_URL is not None
        assert KUSTO_DATABASE_NAME is not None

        auth_mgr = get_auth_manager(use_default_credential=True)
        client = create_kusto_client(
            cluster_url=KUSTO_CLUSTER_URL,
            database=KUSTO_DATABASE_NAME,
            auth_manager=auth_mgr,
        )
        return client

    @pytest.mark.asyncio
    async def test_schema_discovery_complete_workflow(self, kusto_client):
        """Test complete schema discovery workflow against real Kusto cluster."""
        # Create the Schema Discovery Agent
        agent = await create_schema_discovery_agent(
            kusto_client=kusto_client,
            use_azure=False
        )

        # Use a test provider GUID (this may not exist in the cluster)
        test_provider_guid = "12345678-1234-1234-1234-123456789012"
        test_rule_id = "integration-test-rule"

        # Run schema discovery
        result = await agent.discover_schema(
            provider_guid=test_provider_guid,
            rule_id=test_rule_id
        )

        # Verify result structure (content may be empty if GUID doesn't exist)
        assert isinstance(result, KustoSchemaData)
        assert result.provider_guid == test_provider_guid
        assert isinstance(result.existing_detectors, list)
        assert isinstance(result.schema_fields, list)


# Manual tests for developers
class TestSchemaDiscoveryManual:
    """
    Manual integration tests for Schema Discovery Agent.

    These tests are always skipped in CI but can be run manually
    by developers with access to a test Kusto cluster with real ETW data.
    """

    @pytest.mark.skip(reason="Manual test - requires real cluster and ETW data")
    @pytest.mark.asyncio
    async def test_schema_discovery_with_real_etw_data(self):
        """
        Manual test for schema discovery with real ETW data.

        To run this test:
        1. Set KUSTO_CLUSTER_URL and KUSTO_DATABASE_NAME environment variables
        2. Update provider_guid to match a real ETW provider in your cluster
        3. Run: pytest -v -k test_schema_discovery_with_real_etw_data -s
        """
        cluster_url = os.getenv("KUSTO_CLUSTER_URL")
        database_name = os.getenv("KUSTO_DATABASE_NAME")
        assert cluster_url is not None, "KUSTO_CLUSTER_URL must be set"
        assert database_name is not None, "KUSTO_DATABASE_NAME must be set"

        auth_mgr = get_auth_manager(use_default_credential=True)
        kusto_client = create_kusto_client(
            cluster_url=cluster_url,
            database=database_name,
            auth_manager=auth_mgr,
        )

        # Create agent
        agent = await create_schema_discovery_agent(
            kusto_client=kusto_client,
            use_azure=False
        )

        # Use a real provider GUID from your cluster
        provider_guid = "YOUR-REAL-PROVIDER-GUID-HERE"
        rule_id = "manual-test-rule"

        # Run schema discovery
        result = await agent.discover_schema(
            provider_guid=provider_guid,
            rule_id=rule_id
        )

        # Display results
        print(f"\n{'='*70}")
        print(f"Provider GUID: {result.provider_guid}")
        print(f"Existing Detectors: {len(result.existing_detectors)}")
        if result.existing_detectors:
            for detector in result.existing_detectors:
                print(f"  - {detector}")
        print(f"Schema Fields: {len(result.schema_fields)}")
        if result.schema_fields:
            for field in result.schema_fields[:10]:  # Show first 10
                print(f"  - {field.name}: {field.data_type}")
        print(f"{'='*70}\n")

        # Verify structure
        assert isinstance(result, KustoSchemaData)
        assert result.provider_guid == provider_guid
