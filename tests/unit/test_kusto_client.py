"""
Unit tests for the Azure Kusto Client Wrapper.

Tests initialization, query execution, error handling, retry logic, and timeout enforcement.
"""

import pytest
from unittest.mock import Mock, patch
from azure.kusto.data.exceptions import KustoServiceError

from shared.kusto_client import KustoClientWrapper, create_kusto_client
from shared.auth import AuthenticationManager


class TestKustoClientWrapperInitialization:
    """Tests for KustoClientWrapper initialization."""

    def test_init_with_auth_manager(self):
        """Test initialization with AuthenticationManager."""
        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_client = Mock()
        mock_auth_mgr.get_kusto_client.return_value = mock_client

        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        assert wrapper.cluster_url == "https://test.kusto.windows.net"
        assert wrapper.database == "test-db"
        assert wrapper.auth_manager == mock_auth_mgr
        assert wrapper.client == mock_client
        mock_auth_mgr.get_kusto_client.assert_called_once_with(
            "https://test.kusto.windows.net", "test-db"
        )

    @patch("shared.kusto_client.KustoClient")
    @patch("shared.kusto_client.KustoConnectionStringBuilder.with_aad_device_authentication")
    def test_init_without_auth_manager(self, mock_kcsb, mock_kusto_client):
        """Test initialization without AuthenticationManager (fallback)."""
        mock_connection_string = Mock()
        mock_kcsb.return_value = mock_connection_string
        mock_client_instance = Mock()
        mock_kusto_client.return_value = mock_client_instance

        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
        )

        assert wrapper.cluster_url == "https://test.kusto.windows.net"
        assert wrapper.database == "test-db"
        assert wrapper.auth_manager is None
        mock_kcsb.assert_called_once_with("https://test.kusto.windows.net")
        mock_kusto_client.assert_called_once_with(mock_connection_string)


class TestKustoClientWrapperQueryExecution:
    """Tests for query execution functionality."""

    def test_execute_query_success(self):
        """Test successful query execution."""
        # Mock Kusto client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_primary_table = [
            {"Column1": "Value1", "Column2": 123},
            {"Column1": "Value2", "Column2": 456},
        ]
        mock_response.primary_results = [mock_primary_table]
        mock_client.execute.return_value = mock_response

        # Create wrapper
        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = mock_client
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        # Execute query
        query = "MyTable | take 10"
        results = wrapper.execute_query(query)

        # Verify results
        assert len(results) == 2
        assert results[0] == {"Column1": "Value1", "Column2": 123}
        assert results[1] == {"Column1": "Value2", "Column2": 456}
        mock_client.execute.assert_called_once_with("test-db", query)

    def test_execute_query_with_custom_timeout(self):
        """Test query execution with custom timeout."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.primary_results = [[]]
        mock_client.execute.return_value = mock_response

        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = mock_client
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        # Execute query with custom timeout
        query = "MyTable | take 10"
        results = wrapper.execute_query(query, timeout_seconds=60)

        assert results == []
        mock_client.execute.assert_called_once_with("test-db", query)

    def test_execute_query_empty_results(self):
        """Test query execution with empty results."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.primary_results = [[]]  # Empty results
        mock_client.execute.return_value = mock_response

        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = mock_client
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        query = "MyTable | where 1 == 0"
        results = wrapper.execute_query(query)

        assert results == []
        mock_client.execute.assert_called_once_with("test-db", query)

    def test_execute_query_no_primary_results(self):
        """Test query execution with no primary results."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.primary_results = None
        mock_client.execute.return_value = mock_response

        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = mock_client
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        query = ".show databases"
        results = wrapper.execute_query(query)

        assert results == []


class TestKustoClientWrapperErrorHandling:
    """Tests for error handling functionality."""

    def test_execute_query_kusto_service_error(self):
        """Test query execution with KustoServiceError."""
        mock_client = Mock()
        mock_client.execute.side_effect = KustoServiceError("Syntax error in query")

        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = mock_client
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        query = "InvalidQuery ||"
        with pytest.raises(KustoServiceError, match="Syntax error in query"):
            wrapper.execute_query(query)

    def test_execute_query_generic_exception(self):
        """Test query execution with generic exception."""
        mock_client = Mock()
        mock_client.execute.side_effect = ValueError("Unexpected error")

        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = mock_client
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        query = "MyTable | take 10"
        with pytest.raises(ValueError, match="Unexpected error"):
            wrapper.execute_query(query)

    def test_execute_query_connection_error(self):
        """Test query execution with ConnectionError."""
        mock_client = Mock()
        mock_client.execute.side_effect = ConnectionError("Network unreachable")

        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = mock_client
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        query = "MyTable | take 10"
        # ConnectionError should trigger retry, but after all retries it should still raise
        with pytest.raises(ConnectionError, match="Network unreachable"):
            wrapper.execute_query(query)


class TestKustoClientWrapperRetryLogic:
    """Tests for retry logic with exponential backoff."""

    def test_retry_on_kusto_service_error(self):
        """Test that transient KustoServiceError triggers retry."""
        mock_client = Mock()
        # First two calls fail, third succeeds
        mock_response = Mock()
        mock_response.primary_results = [[{"Column1": "Success"}]]
        mock_client.execute.side_effect = [
            KustoServiceError("Transient error 1"),
            KustoServiceError("Transient error 2"),
            mock_response,
        ]

        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = mock_client
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        query = "MyTable | take 10"
        results = wrapper.execute_query(query)

        # Should succeed after retries
        assert len(results) == 1
        assert results[0] == {"Column1": "Success"}
        # Should have been called 3 times (2 failures + 1 success)
        assert mock_client.execute.call_count == 3

    def test_retry_on_connection_error(self):
        """Test that ConnectionError triggers retry."""
        mock_client = Mock()
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.primary_results = [[{"Column1": "Success"}]]
        mock_client.execute.side_effect = [
            ConnectionError("Network error"),
            mock_response,
        ]

        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = mock_client
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        query = "MyTable | take 10"
        results = wrapper.execute_query(query)

        # Should succeed after retry
        assert len(results) == 1
        assert mock_client.execute.call_count == 2

    def test_max_retries_exceeded(self):
        """Test that query fails after max retries (3 attempts)."""
        mock_client = Mock()
        # All attempts fail
        mock_client.execute.side_effect = KustoServiceError("Persistent error")

        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = mock_client
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        query = "MyTable | take 10"
        with pytest.raises(KustoServiceError, match="Persistent error"):
            wrapper.execute_query(query)

        # Should have tried 3 times
        assert mock_client.execute.call_count == 3

    def test_no_retry_on_non_retryable_error(self):
        """Test that non-retryable errors don't trigger retry."""
        mock_client = Mock()
        # ValueError is not configured to retry
        mock_client.execute.side_effect = ValueError("Invalid argument")

        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = mock_client
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        query = "MyTable | take 10"
        with pytest.raises(ValueError, match="Invalid argument"):
            wrapper.execute_query(query)

        # Should only try once (no retry)
        assert mock_client.execute.call_count == 1


class TestKustoClientWrapperQueryTemplates:
    """Tests for query template functionality."""

    def test_load_query_template_success(self):
        """Test loading query template with parameters."""
        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = Mock()
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        template = "MyTable | where ProviderGuid == '{provider_guid}' | take {limit}"
        params = {
            "provider_guid": "12345678-1234-1234-1234-123456789012",
            "limit": 100,
        }

        result = wrapper.load_query_template(template, params)

        expected = "MyTable | where ProviderGuid == '12345678-1234-1234-1234-123456789012' | take 100"
        assert result == expected

    def test_load_query_template_missing_parameter(self):
        """Test loading query template with missing parameter."""
        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = Mock()
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        template = "MyTable | where ProviderGuid == '{provider_guid}'"
        params = {}  # Missing provider_guid

        with pytest.raises(ValueError, match="Missing required parameter"):
            wrapper.load_query_template(template, params)

    def test_load_query_template_partial_parameters(self):
        """Test loading query template with partial parameters."""
        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = Mock()
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        template = "MyTable | where ProviderGuid == '{provider_guid}' | take {limit}"
        params = {"provider_guid": "12345678-1234-1234-1234-123456789012"}  # Missing limit

        with pytest.raises(ValueError, match="Missing required parameter"):
            wrapper.load_query_template(template, params)

    def test_load_query_template_no_placeholders(self):
        """Test loading query template with no placeholders."""
        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = Mock()
        wrapper = KustoClientWrapper(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        template = "MyTable | take 10"
        params = {}

        result = wrapper.load_query_template(template, params)

        assert result == "MyTable | take 10"


class TestCreateKustoClient:
    """Tests for the create_kusto_client factory function."""

    def test_create_kusto_client_with_auth_manager(self):
        """Test factory function with AuthenticationManager."""
        mock_auth_mgr = Mock(spec=AuthenticationManager)
        mock_auth_mgr.get_kusto_client.return_value = Mock()

        client = create_kusto_client(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
            auth_manager=mock_auth_mgr,
        )

        assert isinstance(client, KustoClientWrapper)
        assert client.cluster_url == "https://test.kusto.windows.net"
        assert client.database == "test-db"

    @patch("shared.kusto_client.KustoClient")
    @patch("shared.kusto_client.KustoConnectionStringBuilder.with_aad_device_authentication")
    def test_create_kusto_client_without_auth_manager(self, mock_kcsb, mock_kusto_client):
        """Test factory function without AuthenticationManager."""
        mock_kcsb.return_value = Mock()
        mock_kusto_client.return_value = Mock()

        client = create_kusto_client(
            cluster_url="https://test.kusto.windows.net",
            database="test-db",
        )

        assert isinstance(client, KustoClientWrapper)
        assert client.cluster_url == "https://test.kusto.windows.net"
        assert client.database == "test-db"
