"""
Unit tests for Approval Gate Executor using MAF ChatAgent pattern.

Tests user approval logic with mocked ChatAgent and user_input_requests.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock, Mock
import os


class TestApprovalGateExecutor:
    """Tests for approval_gate_executor with MAF ChatAgent pattern."""

    @pytest.mark.asyncio
    async def test_approval_with_user_approval(self):
        """Test approval gate with user approving via y/n prompt."""
        from workflows.detector_workflow import _handle_pr_approval

        # Mock workflow data
        workflow_data = {
            "pr_url": "https://dev.azure.com/test/project/_git/repo/pullrequest/123",
            "pr_id": 123,
            "branch_name": "detector/test_rule",
            "rule_id": "test_rule",
            "provider_guid": "12345678-1234-1234-1234-123456789012",
            "schema_fields": [
                {"name": "EventId", "data_type": "int", "description": "Event ID"}
            ],
            "detector_file_name": "detector_test_rule.py",
            "test_file_name": "test_detector_test_rule.py",
        }

        # Mock OpenAIChatClient
        mock_chat_client = MagicMock()

        # Mock user input request
        mock_user_input_request = MagicMock()
        mock_user_input_request.function_call.name = "proceed_with_pr_deployment"
        mock_user_input_request.create_response = MagicMock(return_value="approval_response")

        # Mock agent run response
        mock_agent_response = MagicMock()
        mock_agent_response.user_input_requests = [mock_user_input_request]

        # Mock ChatAgent
        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_agent_response)
        mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
        mock_agent.__aexit__ = AsyncMock(return_value=None)

        # Patch ChatAgent constructor and input
        with patch("workflows.detector_workflow.ChatAgent", return_value=mock_agent):
            with patch("asyncio.to_thread", return_value="y"):
                result = await _handle_pr_approval(workflow_data, mock_chat_client)

                # Verify approval
                assert result is True

    @pytest.mark.asyncio
    async def test_approval_with_user_rejection(self):
        """Test approval gate with user rejecting via y/n prompt."""
        from workflows.detector_workflow import _handle_pr_approval

        workflow_data = {
            "pr_url": "https://dev.azure.com/test/project/_git/repo/pullrequest/123",
            "pr_id": 123,
            "branch_name": "detector/test_rule",
            "rule_id": "test_rule",
            "provider_guid": "12345678-1234-1234-1234-123456789012",
            "schema_fields": [],
            "detector_file_name": "detector_test_rule.py",
            "test_file_name": "test_detector_test_rule.py",
        }

        mock_chat_client = MagicMock()

        mock_user_input_request = MagicMock()
        mock_user_input_request.function_call.name = "proceed_with_pr_deployment"
        mock_user_input_request.create_response = MagicMock(return_value="approval_response")

        mock_agent_response = MagicMock()
        mock_agent_response.user_input_requests = [mock_user_input_request]

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_agent_response)
        mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
        mock_agent.__aexit__ = AsyncMock(return_value=None)

        with patch("workflows.detector_workflow.ChatAgent", return_value=mock_agent):
            with patch("asyncio.to_thread", return_value="n"):
                result = await _handle_pr_approval(workflow_data, mock_chat_client)

                # Verify rejection
                assert result is False

    @pytest.mark.asyncio
    async def test_approval_with_yes_input(self):
        """Test approval gate accepts 'yes' as approval."""
        from workflows.detector_workflow import _handle_pr_approval

        workflow_data = {
            "pr_url": "https://dev.azure.com/test/project/_git/repo/pullrequest/123",
            "pr_id": 123,
            "branch_name": "detector/test_rule",
            "rule_id": "test_rule",
            "provider_guid": "12345678-1234-1234-1234-123456789012",
            "schema_fields": [],
            "detector_file_name": "detector_test_rule.py",
            "test_file_name": "test_detector_test_rule.py",
        }

        mock_chat_client = MagicMock()

        mock_user_input_request = MagicMock()
        mock_user_input_request.function_call.name = "proceed_with_pr_deployment"
        mock_user_input_request.create_response = MagicMock(return_value="approval_response")

        mock_agent_response = MagicMock()
        mock_agent_response.user_input_requests = [mock_user_input_request]

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_agent_response)
        mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
        mock_agent.__aexit__ = AsyncMock(return_value=None)

        with patch("workflows.detector_workflow.ChatAgent", return_value=mock_agent):
            with patch("asyncio.to_thread", return_value="yes"):
                result = await _handle_pr_approval(workflow_data, mock_chat_client)

                assert result is True

    @pytest.mark.asyncio
    async def test_approval_with_auto_approve_env_var(self):
        """Test approval gate with MAF_AUTO_APPROVE environment variable."""
        from workflows.detector_workflow import _handle_pr_approval

        workflow_data = {
            "pr_url": "https://dev.azure.com/test/project/_git/repo/pullrequest/123",
            "pr_id": 123,
            "branch_name": "detector/test_rule",
            "rule_id": "test_rule",
            "provider_guid": "12345678-1234-1234-1234-123456789012",
            "schema_fields": [],
            "detector_file_name": "detector_test_rule.py",
            "test_file_name": "test_detector_test_rule.py",
        }

        mock_chat_client = MagicMock()

        # Set MAF_AUTO_APPROVE environment variable
        with patch.dict(os.environ, {"MAF_AUTO_APPROVE": "true"}):
            result = await _handle_pr_approval(workflow_data, mock_chat_client)

            # Verify auto-approval (should not even call ChatAgent)
            assert result is True

    @pytest.mark.asyncio
    async def test_approval_with_auto_approve_false(self):
        """Test approval gate with MAF_AUTO_APPROVE=false (should prompt)."""
        from workflows.detector_workflow import _handle_pr_approval

        workflow_data = {
            "pr_url": "https://dev.azure.com/test/project/_git/repo/pullrequest/123",
            "pr_id": 123,
            "branch_name": "detector/test_rule",
            "rule_id": "test_rule",
            "provider_guid": "12345678-1234-1234-1234-123456789012",
            "schema_fields": [],
            "detector_file_name": "detector_test_rule.py",
            "test_file_name": "test_detector_test_rule.py",
        }

        mock_chat_client = MagicMock()

        mock_user_input_request = MagicMock()
        mock_user_input_request.function_call.name = "proceed_with_pr_deployment"
        mock_user_input_request.create_response = MagicMock(return_value="approval_response")

        mock_agent_response = MagicMock()
        mock_agent_response.user_input_requests = [mock_user_input_request]

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_agent_response)
        mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
        mock_agent.__aexit__ = AsyncMock(return_value=None)

        # Set MAF_AUTO_APPROVE to false, should still prompt for input
        with patch.dict(os.environ, {"MAF_AUTO_APPROVE": "false"}):
            with patch("workflows.detector_workflow.ChatAgent", return_value=mock_agent):
                with patch("asyncio.to_thread", return_value="y"):
                    result = await _handle_pr_approval(workflow_data, mock_chat_client)

                    # Verify manual approval was used
                    assert result is True

    @pytest.mark.asyncio
    async def test_approval_case_insensitive(self):
        """Test approval gate with case variations."""
        from workflows.detector_workflow import _handle_pr_approval

        workflow_data = {
            "pr_url": "https://dev.azure.com/test/project/_git/repo/pullrequest/123",
            "pr_id": 123,
            "branch_name": "detector/test_rule",
            "rule_id": "test_rule",
            "provider_guid": "12345678-1234-1234-1234-123456789012",
            "schema_fields": [],
            "detector_file_name": "detector_test_rule.py",
            "test_file_name": "test_detector_test_rule.py",
        }

        mock_chat_client = MagicMock()

        mock_user_input_request = MagicMock()
        mock_user_input_request.function_call.name = "proceed_with_pr_deployment"
        mock_user_input_request.create_response = MagicMock(return_value="approval_response")

        mock_agent_response = MagicMock()
        mock_agent_response.user_input_requests = [mock_user_input_request]

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_agent_response)
        mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
        mock_agent.__aexit__ = AsyncMock(return_value=None)

        # Test with uppercase Y
        with patch("workflows.detector_workflow.ChatAgent", return_value=mock_agent):
            with patch("asyncio.to_thread", return_value="Y"):
                result = await _handle_pr_approval(workflow_data, mock_chat_client)
                assert result is True

    @pytest.mark.asyncio
    async def test_approval_with_whitespace(self):
        """Test approval gate with whitespace in input."""
        from workflows.detector_workflow import _handle_pr_approval

        workflow_data = {
            "pr_url": "https://dev.azure.com/test/project/_git/repo/pullrequest/123",
            "pr_id": 123,
            "branch_name": "detector/test_rule",
            "rule_id": "test_rule",
            "provider_guid": "12345678-1234-1234-1234-123456789012",
            "schema_fields": [],
            "detector_file_name": "detector_test_rule.py",
            "test_file_name": "test_detector_test_rule.py",
        }

        mock_chat_client = MagicMock()

        mock_user_input_request = MagicMock()
        mock_user_input_request.function_call.name = "proceed_with_pr_deployment"
        mock_user_input_request.create_response = MagicMock(return_value="approval_response")

        mock_agent_response = MagicMock()
        mock_agent_response.user_input_requests = [mock_user_input_request]

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_agent_response)
        mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
        mock_agent.__aexit__ = AsyncMock(return_value=None)

        # Test with leading/trailing whitespace
        with patch("workflows.detector_workflow.ChatAgent", return_value=mock_agent):
            with patch("asyncio.to_thread", return_value="  y  "):
                result = await _handle_pr_approval(workflow_data, mock_chat_client)
                assert result is True

    @pytest.mark.asyncio
    async def test_approval_with_no_user_input_requests(self):
        """Test approval gate when agent doesn't return user_input_requests."""
        from workflows.detector_workflow import _handle_pr_approval

        workflow_data = {
            "pr_url": "https://dev.azure.com/test/project/_git/repo/pullrequest/123",
            "pr_id": 123,
            "branch_name": "detector/test_rule",
            "rule_id": "test_rule",
            "provider_guid": "12345678-1234-1234-1234-123456789012",
            "schema_fields": [],
            "detector_file_name": "detector_test_rule.py",
            "test_file_name": "test_detector_test_rule.py",
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
            result = await _handle_pr_approval(workflow_data, mock_chat_client)

            # Should default to rejection for safety
            assert result is False
