"""
Unit tests for Deployment Verification Executor.

Tests polling logic and deployment detection with mocked Azure Repos API.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock, Mock


def create_mock_config():
    """Helper to create mock config with Azure settings."""
    mock_config = MagicMock()
    mock_config.azure.azure_devops_org = "test-org"
    mock_config.azure.azure_devops_project = "test-project"
    mock_config.azure.azure_devops_repo = "test-repo"
    return mock_config


class TestDeploymentVerification:
    """Tests for deployment_verification_executor and polling logic."""

    @pytest.mark.asyncio
    async def test_poll_pr_merge_status_success(self):
        """Test successful PR merge detection."""
        from workflows.detector_workflow import _poll_pr_merge_status

        workflow_data = {
            "pr_id": 123,
            "pr_url": "https://dev.azure.com/test/project/_git/repo/pullrequest/123",
        }

        # Mock PR status as completed
        mock_pr_status = {
            "pr_id": 123,
            "status": "completed",
            "is_completed": True,
            "is_active": False,
            "is_abandoned": False,
        }

        with patch("shared.repos_utils.get_pull_request_status", return_value=mock_pr_status):
            with patch("shared.config.get_config", return_value=create_mock_config()):
                with patch("shared.auth.get_auth_manager"):
                    success, message = await _poll_pr_merge_status(
                        workflow_data,
                        poll_interval_seconds=1,  # Fast for testing
                        max_wait_minutes=1,
                    )

                    assert success is True
                    assert "merged successfully" in message.lower()

    @pytest.mark.asyncio
    async def test_poll_pr_merge_status_abandoned(self):
        """Test PR abandoned detection."""
        from workflows.detector_workflow import _poll_pr_merge_status

        workflow_data = {
            "pr_id": 123,
        }

        # Mock PR status as abandoned
        mock_pr_status = {
            "pr_id": 123,
            "status": "abandoned",
            "is_completed": False,
            "is_active": False,
            "is_abandoned": True,
        }

        with patch("shared.repos_utils.get_pull_request_status", return_value=mock_pr_status):
            with patch("shared.config.get_config", return_value=create_mock_config()):
                with patch("shared.auth.get_auth_manager"):
                    success, message = await _poll_pr_merge_status(
                        workflow_data,
                        poll_interval_seconds=1,
                        max_wait_minutes=1,
                    )

                    assert success is False
                    assert "abandoned" in message.lower()

    @pytest.mark.asyncio
    async def test_poll_pr_merge_status_timeout(self):
        """Test timeout when PR never merges."""
        from workflows.detector_workflow import _poll_pr_merge_status

        workflow_data = {
            "pr_id": 123,
        }

        # Mock PR status as always active (never completes)
        mock_pr_status = {
            "pr_id": 123,
            "status": "active",
            "is_completed": False,
            "is_active": True,
            "is_abandoned": False,
        }

        with patch("shared.repos_utils.get_pull_request_status", return_value=mock_pr_status):
            with patch("shared.config.get_config", return_value=create_mock_config()):
                with patch("shared.auth.get_auth_manager"):
                    # Very short timeout for testing
                    success, message = await _poll_pr_merge_status(
                        workflow_data,
                        poll_interval_seconds=1,
                        max_wait_minutes=0.05,  # 3 seconds
                    )

                    assert success is False
                    assert ("not detected" in message.lower()) or ("verify manually" in message.lower())

    @pytest.mark.asyncio
    async def test_poll_pr_merge_status_no_pr_id(self):
        """Test handling of missing PR ID."""
        from workflows.detector_workflow import _poll_pr_merge_status

        workflow_data = {}  # No PR ID

        success, message = await _poll_pr_merge_status(workflow_data)

        assert success is False
        assert "no pr id" in message.lower()

    @pytest.mark.asyncio
    async def test_poll_pr_merge_status_with_retry(self):
        """Test exponential backoff retry on errors."""
        from workflows.detector_workflow import _poll_pr_merge_status

        workflow_data = {
            "pr_id": 123,
        }

        # Mock to fail once, then succeed
        call_count = [0]

        def mock_get_pr_status(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Temporary API error")
            return {
                "pr_id": 123,
                "status": "completed",
                "is_completed": True,
                "is_active": False,
                "is_abandoned": False,
            }

        with patch("shared.repos_utils.get_pull_request_status", side_effect=mock_get_pr_status):
            with patch("shared.config.get_config", return_value=create_mock_config()):
                with patch("shared.auth.get_auth_manager"):
                    success, message = await _poll_pr_merge_status(
                        workflow_data,
                        poll_interval_seconds=1,
                        max_wait_minutes=1,
                    )

                    # Should succeed after retry
                    assert success is True
                    assert call_count[0] == 2  # Failed once, then succeeded
