"""
Unit tests for Results Analysis Executor.

Tests Kusto query execution, metrics analysis, and user confirmation with mocked responses.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock, Mock
import os


def create_mock_config():
    """Helper to create mock config with Kusto settings."""
    mock_config = MagicMock()
    mock_config.azure.kusto_cluster_url = "https://test.kusto.windows.net"
    mock_config.azure.kusto_database_name = "test-db"
    mock_config.azure.azure_devops_org = "test-org"
    mock_config.azure.azure_devops_project = "test-project"
    mock_config.azure.azure_devops_repo = "test-repo"
    return mock_config


class TestFetchAndAnalyzeResults:
    """Tests for _fetch_and_analyze_results function."""

    @pytest.mark.asyncio
    async def test_fetch_results_success(self):
        """Test successful results fetch and analysis from Kusto."""
        from workflows.detector_workflow import _fetch_and_analyze_results

        workflow_data = {
            "rule_id": "test_rule",
            "deployment_detected": True,
            "deployment_timestamp": "2024-01-01T12:00:00",
        }

        # Mock Kusto query results
        mock_kusto_results = [
            {"EventCount": 10, "ErrorCount": 0, "UniqueHosts": 3},
            {"EventCount": 15, "ErrorCount": 1, "UniqueHosts": 5},
            {"EventCount": 5, "ErrorCount": 0, "UniqueHosts": 2},
        ]

        mock_kusto_client = MagicMock()
        mock_kusto_client.load_query_template.return_value = "SELECT * FROM DetectorResults"
        mock_kusto_client.execute_query.return_value = mock_kusto_results

        with patch("workflows.detector_workflow.get_config", return_value=create_mock_config()):
            with patch("workflows.detector_workflow.get_auth_manager"):
                with patch("workflows.detector_workflow.create_kusto_client", return_value=mock_kusto_client):
                    metrics, summary = await _fetch_and_analyze_results(workflow_data)

        # Verify metrics
        assert metrics["status"] == "success"
        assert metrics["total_events"] == 30  # 10 + 15 + 5
        assert metrics["error_count"] == 1
        assert metrics["unique_hosts"] == 5  # max of [3, 5, 2]
        assert metrics["error_rate"] == 3.33  # 1/30 * 100, rounded to 2 decimals
        assert metrics["time_buckets"] == 3

        # Verify summary
        assert "30 events" in summary
        assert "5 unique hosts" in summary
        assert "1 errors" in summary

    @pytest.mark.asyncio
    async def test_fetch_results_no_data(self):
        """Test results fetch when no data is returned from Kusto."""
        from workflows.detector_workflow import _fetch_and_analyze_results

        workflow_data = {
            "rule_id": "test_rule",
            "deployment_detected": True,
            "deployment_timestamp": "2024-01-01T12:00:00",
        }

        # Mock Kusto returning empty results
        mock_kusto_client = MagicMock()
        mock_kusto_client.load_query_template.return_value = "SELECT * FROM DetectorResults"
        mock_kusto_client.execute_query.return_value = []

        with patch("workflows.detector_workflow.get_config", return_value=create_mock_config()):
            with patch("workflows.detector_workflow.get_auth_manager"):
                with patch("workflows.detector_workflow.create_kusto_client", return_value=mock_kusto_client):
                    metrics, summary = await _fetch_and_analyze_results(workflow_data)

        # Verify metrics for no data
        assert metrics["status"] == "no_data"
        assert metrics["total_events"] == 0
        assert metrics["error_count"] == 0
        assert metrics["unique_hosts"] == 0
        assert "No detector results found" in summary

    @pytest.mark.asyncio
    async def test_fetch_results_deployment_not_detected(self):
        """Test results fetch when deployment was not detected."""
        from workflows.detector_workflow import _fetch_and_analyze_results

        workflow_data = {
            "rule_id": "test_rule",
            "deployment_detected": False,
        }

        metrics, summary = await _fetch_and_analyze_results(workflow_data)

        # Should skip analysis
        assert metrics["status"] == "skipped"
        assert metrics["reason"] == "deployment_not_detected"
        assert "Deployment was not detected" in summary

    @pytest.mark.asyncio
    async def test_fetch_results_kusto_not_configured(self):
        """Test results fetch when Kusto is not configured."""
        from workflows.detector_workflow import _fetch_and_analyze_results

        workflow_data = {
            "rule_id": "test_rule",
            "deployment_detected": True,
        }

        # Mock config with no Kusto settings
        mock_config = MagicMock()
        mock_config.azure.kusto_cluster_url = None
        mock_config.azure.kusto_database_name = None

        with patch("workflows.detector_workflow.get_config", return_value=mock_config):
            metrics, summary = await _fetch_and_analyze_results(workflow_data)

        # Should return placeholder metrics
        assert metrics["status"] == "placeholder"
        assert metrics["total_events"] == 42
        assert metrics["error_count"] == 0
        assert metrics["unique_hosts"] == 5
        assert "placeholder metrics" in summary

    @pytest.mark.asyncio
    async def test_fetch_results_kusto_error(self):
        """Test results fetch when Kusto query fails."""
        from workflows.detector_workflow import _fetch_and_analyze_results

        workflow_data = {
            "rule_id": "test_rule",
            "deployment_detected": True,
            "deployment_timestamp": "2024-01-01T12:00:00",
        }

        # Mock Kusto client that raises an error
        mock_kusto_client = MagicMock()
        mock_kusto_client.load_query_template.return_value = "SELECT * FROM DetectorResults"
        mock_kusto_client.execute_query.side_effect = Exception("Kusto connection timeout")

        with patch("workflows.detector_workflow.get_config", return_value=create_mock_config()):
            with patch("workflows.detector_workflow.get_auth_manager"):
                with patch("workflows.detector_workflow.create_kusto_client", return_value=mock_kusto_client):
                    metrics, summary = await _fetch_and_analyze_results(workflow_data)

        # Should return error status
        assert metrics["status"] == "error"
        assert "Kusto connection timeout" in metrics["error"]
        assert "Error fetching results" in summary

    @pytest.mark.asyncio
    async def test_fetch_results_zero_error_rate(self):
        """Test error rate calculation when no errors."""
        from workflows.detector_workflow import _fetch_and_analyze_results

        workflow_data = {
            "rule_id": "test_rule",
            "deployment_detected": True,
            "deployment_timestamp": "2024-01-01T12:00:00",
        }

        # Mock Kusto results with no errors
        mock_kusto_results = [
            {"EventCount": 100, "ErrorCount": 0, "UniqueHosts": 10},
        ]

        mock_kusto_client = MagicMock()
        mock_kusto_client.load_query_template.return_value = "SELECT * FROM DetectorResults"
        mock_kusto_client.execute_query.return_value = mock_kusto_results

        with patch("workflows.detector_workflow.get_config", return_value=create_mock_config()):
            with patch("workflows.detector_workflow.get_auth_manager"):
                with patch("workflows.detector_workflow.create_kusto_client", return_value=mock_kusto_client):
                    metrics, summary = await _fetch_and_analyze_results(workflow_data)

        # Verify error rate is 0
        assert metrics["error_rate"] == 0.0
        assert "No errors detected" in summary


class TestHandleResultsConfirmation:
    """Tests for _handle_results_confirmation function."""

    @pytest.mark.asyncio
    async def test_confirmation_with_user_yes(self):
        """Test results confirmation with user confirming."""
        from workflows.detector_workflow import _handle_results_confirmation

        workflow_data = {
            "rule_id": "test_rule",
        }

        metrics = {
            "status": "success",
            "total_events": 30,
            "error_count": 1,
            "error_rate": 3.33,
            "unique_hosts": 5,
            "time_buckets": 3,
        }

        mock_chat_client = MagicMock()

        # Mock user input request
        mock_user_input_request = MagicMock()
        mock_user_input_request.function_call.name = "confirm_detector_results"
        mock_user_input_request.create_response = MagicMock(return_value="confirmation_response")

        # Mock agent run response
        mock_agent_response = MagicMock()
        mock_agent_response.user_input_requests = [mock_user_input_request]

        # Mock ChatAgent
        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_agent_response)
        mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
        mock_agent.__aexit__ = AsyncMock(return_value=None)

        with patch("workflows.detector_workflow.ChatAgent", return_value=mock_agent):
            with patch("asyncio.to_thread", return_value="yes"):
                result = await _handle_results_confirmation(workflow_data, metrics, mock_chat_client)

        # Verify confirmation
        assert result is True

    @pytest.mark.asyncio
    async def test_confirmation_with_user_no(self):
        """Test results confirmation with user rejecting."""
        from workflows.detector_workflow import _handle_results_confirmation

        workflow_data = {
            "rule_id": "test_rule",
        }

        metrics = {
            "status": "success",
            "total_events": 5,
            "error_count": 10,
            "error_rate": 200.0,
            "unique_hosts": 1,
            "time_buckets": 1,
        }

        mock_chat_client = MagicMock()

        mock_user_input_request = MagicMock()
        mock_user_input_request.function_call.name = "confirm_detector_results"
        mock_user_input_request.create_response = MagicMock(return_value="confirmation_response")

        mock_agent_response = MagicMock()
        mock_agent_response.user_input_requests = [mock_user_input_request]

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_agent_response)
        mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
        mock_agent.__aexit__ = AsyncMock(return_value=None)

        with patch("workflows.detector_workflow.ChatAgent", return_value=mock_agent):
            with patch("asyncio.to_thread", return_value="no"):
                result = await _handle_results_confirmation(workflow_data, metrics, mock_chat_client)

        # Verify rejection
        assert result is False

    @pytest.mark.asyncio
    async def test_confirmation_with_auto_confirm_env_var(self):
        """Test results confirmation with auto-confirm environment variable."""
        from workflows.detector_workflow import _handle_results_confirmation

        workflow_data = {
            "rule_id": "test_rule",
        }

        metrics = {
            "status": "success",
            "total_events": 30,
            "error_count": 0,
            "error_rate": 0.0,
            "unique_hosts": 5,
            "time_buckets": 3,
        }

        mock_chat_client = MagicMock()

        # Set auto-confirm environment variable
        with patch.dict(os.environ, {"MAF_AUTO_CONFIRM_RESULTS": "true"}):
            result = await _handle_results_confirmation(workflow_data, metrics, mock_chat_client)

        # Verify auto-confirmation (should not even call ChatAgent)
        assert result is True

    @pytest.mark.asyncio
    async def test_confirmation_with_y_input(self):
        """Test results confirmation accepts 'y' as confirmation."""
        from workflows.detector_workflow import _handle_results_confirmation

        workflow_data = {
            "rule_id": "test_rule",
        }

        metrics = {
            "status": "placeholder",
            "total_events": 42,
            "error_count": 0,
            "unique_hosts": 5,
        }

        mock_chat_client = MagicMock()

        mock_user_input_request = MagicMock()
        mock_user_input_request.function_call.name = "confirm_detector_results"
        mock_user_input_request.create_response = MagicMock(return_value="confirmation_response")

        mock_agent_response = MagicMock()
        mock_agent_response.user_input_requests = [mock_user_input_request]

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_agent_response)
        mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
        mock_agent.__aexit__ = AsyncMock(return_value=None)

        with patch("workflows.detector_workflow.ChatAgent", return_value=mock_agent):
            with patch("asyncio.to_thread", return_value="y"):
                result = await _handle_results_confirmation(workflow_data, metrics, mock_chat_client)

        assert result is True

    @pytest.mark.asyncio
    async def test_confirmation_case_insensitive(self):
        """Test results confirmation with case variations."""
        from workflows.detector_workflow import _handle_results_confirmation

        workflow_data = {
            "rule_id": "test_rule",
        }

        metrics = {
            "status": "success",
            "total_events": 10,
            "error_count": 0,
            "error_rate": 0.0,
            "unique_hosts": 3,
            "time_buckets": 1,
        }

        mock_chat_client = MagicMock()

        mock_user_input_request = MagicMock()
        mock_user_input_request.function_call.name = "confirm_detector_results"
        mock_user_input_request.create_response = MagicMock(return_value="confirmation_response")

        mock_agent_response = MagicMock()
        mock_agent_response.user_input_requests = [mock_user_input_request]

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_agent_response)
        mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
        mock_agent.__aexit__ = AsyncMock(return_value=None)

        # Test with uppercase YES
        with patch("workflows.detector_workflow.ChatAgent", return_value=mock_agent):
            with patch("asyncio.to_thread", return_value="YES"):
                result = await _handle_results_confirmation(workflow_data, metrics, mock_chat_client)
                assert result is True

    @pytest.mark.asyncio
    async def test_confirmation_with_whitespace(self):
        """Test results confirmation with whitespace in input."""
        from workflows.detector_workflow import _handle_results_confirmation

        workflow_data = {
            "rule_id": "test_rule",
        }

        metrics = {
            "status": "success",
            "total_events": 10,
            "error_count": 0,
            "error_rate": 0.0,
            "unique_hosts": 3,
            "time_buckets": 1,
        }

        mock_chat_client = MagicMock()

        mock_user_input_request = MagicMock()
        mock_user_input_request.function_call.name = "confirm_detector_results"
        mock_user_input_request.create_response = MagicMock(return_value="confirmation_response")

        mock_agent_response = MagicMock()
        mock_agent_response.user_input_requests = [mock_user_input_request]

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_agent_response)
        mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
        mock_agent.__aexit__ = AsyncMock(return_value=None)

        # Test with leading/trailing whitespace
        with patch("workflows.detector_workflow.ChatAgent", return_value=mock_agent):
            with patch("asyncio.to_thread", return_value="  yes  "):
                result = await _handle_results_confirmation(workflow_data, metrics, mock_chat_client)
                assert result is True

    @pytest.mark.asyncio
    async def test_confirmation_with_no_user_input_requests(self):
        """Test confirmation when agent doesn't return user_input_requests."""
        from workflows.detector_workflow import _handle_results_confirmation

        workflow_data = {
            "rule_id": "test_rule",
        }

        metrics = {
            "status": "success",
            "total_events": 10,
            "error_count": 0,
            "error_rate": 0.0,
            "unique_hosts": 3,
            "time_buckets": 1,
        }

        mock_chat_client = MagicMock()

        # Mock agent response with no user_input_requests
        mock_agent_response = MagicMock()
        mock_agent_response.user_input_requests = []

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_agent_response)
        mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
        mock_agent.__aexit__ = AsyncMock(return_value=None)

        with patch("workflows.detector_workflow.ChatAgent", return_value=mock_agent):
            result = await _handle_results_confirmation(workflow_data, metrics, mock_chat_client)

        # Should default to rejection for safety
        assert result is False
