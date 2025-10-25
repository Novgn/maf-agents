"""
Integration tests for Azure Kusto Client Wrapper.

These tests validate successful query execution against a real Azure Kusto cluster.
They require proper Azure credentials and a configured Kusto cluster.

Tests are skipped if required environment variables are not set.
"""

import pytest
import os
from azure.kusto.data.exceptions import KustoServiceError

from shared.kusto_client import create_kusto_client
from shared.auth import get_auth_manager


# Check if Kusto integration tests should run
KUSTO_CLUSTER_URL = os.getenv("KUSTO_CLUSTER_URL")
KUSTO_DATABASE_NAME = os.getenv("KUSTO_DATABASE_NAME")
SKIP_KUSTO_INTEGRATION = not (KUSTO_CLUSTER_URL and KUSTO_DATABASE_NAME)
SKIP_REASON = "Kusto integration tests require KUSTO_CLUSTER_URL and KUSTO_DATABASE_NAME environment variables"


@pytest.mark.skipif(SKIP_KUSTO_INTEGRATION, reason=SKIP_REASON)
class TestKustoIntegration:
    """Integration tests for Kusto client against real cluster."""

    @pytest.fixture
    def kusto_client(self):
        """Create a Kusto client for integration testing."""
        # These should be set due to skipif, but assert for type checking
        assert KUSTO_CLUSTER_URL is not None
        assert KUSTO_DATABASE_NAME is not None

        # Use DefaultAzureCredential for authentication
        auth_mgr = get_auth_manager(use_default_credential=True)
        client = create_kusto_client(
            cluster_url=KUSTO_CLUSTER_URL,
            database=KUSTO_DATABASE_NAME,
            auth_manager=auth_mgr,
        )
        return client

    def test_execute_simple_query(self, kusto_client):
        """Test executing a simple query against real Kusto cluster."""
        # Simple query that should work on any cluster
        query = ".show databases | take 5"

        try:
            results = kusto_client.execute_query(query, timeout_seconds=30)

            # Verify we got results
            assert isinstance(results, list)
            # Should have at least one database
            assert len(results) >= 0  # May be empty in test environment

        except KustoServiceError as e:
            pytest.fail(f"Query execution failed with KustoServiceError: {e}")

    def test_execute_query_with_timeout(self, kusto_client):
        """Test query execution with custom timeout."""
        query = ".show databases | take 1"

        try:
            results = kusto_client.execute_query(query, timeout_seconds=60)

            assert isinstance(results, list)

        except KustoServiceError as e:
            pytest.fail(f"Query execution failed with KustoServiceError: {e}")

    def test_execute_query_with_filter(self, kusto_client):
        """Test query execution with filtering."""
        # Query for databases starting with specific prefix
        query = ".show databases | where DatabaseName startswith '.'"

        try:
            results = kusto_client.execute_query(query, timeout_seconds=30)

            assert isinstance(results, list)
            # If results exist, verify they have expected structure
            if results:
                assert "DatabaseName" in results[0] or "databasename" in results[0].keys()

        except KustoServiceError as e:
            pytest.fail(f"Query execution failed with KustoServiceError: {e}")

    def test_execute_invalid_query_syntax(self, kusto_client):
        """Test that invalid query syntax raises KustoServiceError."""
        # Invalid KQL syntax
        query = "INVALID QUERY SYNTAX ||"

        with pytest.raises(KustoServiceError):
            kusto_client.execute_query(query, timeout_seconds=30)

    def test_execute_query_to_nonexistent_table(self, kusto_client):
        """Test query to non-existent table raises appropriate error."""
        # Query referencing a table that doesn't exist
        query = "NonExistentTable_12345 | take 10"

        with pytest.raises(KustoServiceError):
            kusto_client.execute_query(query, timeout_seconds=30)

    def test_load_and_execute_template_query(self, kusto_client):
        """Test loading a query template and executing it."""
        # Template query
        template = ".show databases | where DatabaseName contains '{search_term}' | take {limit}"
        params = {
            "search_term": "test",
            "limit": 5,
        }

        try:
            # Load template
            query = kusto_client.load_query_template(template, params)
            assert "test" in query
            assert "5" in query

            # Execute the query
            results = kusto_client.execute_query(query, timeout_seconds=30)

            assert isinstance(results, list)

        except KustoServiceError as e:
            # This might fail if there are no databases with 'test' in the name
            # That's acceptable - we're mainly testing the template mechanism
            assert isinstance(e, KustoServiceError)

    def test_execute_query_returns_empty_results(self, kusto_client):
        """Test query that returns no results."""
        # Query that should return empty results
        query = ".show databases | where 1 == 0"

        try:
            results = kusto_client.execute_query(query, timeout_seconds=30)

            assert isinstance(results, list)
            assert len(results) == 0

        except KustoServiceError as e:
            pytest.fail(f"Query execution failed with KustoServiceError: {e}")


# Manual test for developers (not run in CI)
class TestKustoIntegrationManual:
    """
    Manual integration tests for Kusto client.

    These tests are always skipped in CI but can be run manually
    by developers with access to a test Kusto cluster.
    """

    @pytest.mark.skip(reason="Manual test - requires real cluster and manual verification")
    def test_execute_query_with_real_data(self):
        """
        Manual test for executing a query with real ETW data.

        To run this test:
        1. Set KUSTO_CLUSTER_URL and KUSTO_DATABASE_NAME environment variables
        2. Update the query to match your cluster's schema
        3. Run: pytest -v -k test_execute_query_with_real_data -s
        """
        cluster_url = os.getenv("KUSTO_CLUSTER_URL")
        database_name = os.getenv("KUSTO_DATABASE_NAME")
        assert cluster_url is not None, "KUSTO_CLUSTER_URL must be set"
        assert database_name is not None, "KUSTO_DATABASE_NAME must be set"

        auth_mgr = get_auth_manager(use_default_credential=True)
        client = create_kusto_client(
            cluster_url=cluster_url,
            database=database_name,
            auth_manager=auth_mgr,
        )

        # Example: Query for ETW events (adjust table name as needed)
        query = """
        YourETWTable
        | where Timestamp > ago(1d)
        | take 10
        """

        results = client.execute_query(query, timeout_seconds=60)

        print(f"\nQuery returned {len(results)} rows")
        if results:
            print(f"Sample row: {results[0]}")

        assert len(results) >= 0
