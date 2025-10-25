"""
Integration tests for Azure Repos utility functions.

These tests require actual Azure DevOps configuration and will be skipped
if the required environment variables are not set.
"""

import pytest
import os
from datetime import datetime

from shared.auth import get_auth_manager
from shared.config import get_config
from shared.repos_utils import (
    create_branch,
    commit_and_push_files,
    create_pull_request,
    get_pull_request_status,
)

# Skip all tests if Azure DevOps is not configured
pytestmark = pytest.mark.skipif(
    not all([
        os.getenv("AZURE_DEVOPS_ORG"),
        os.getenv("AZURE_DEVOPS_PROJECT"),
        os.getenv("AZURE_DEVOPS_REPO"),
    ]),
    reason="Azure DevOps not configured (set AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT, AZURE_DEVOPS_REPO)",
)


@pytest.fixture
def azure_connection():
    """
    Create an authenticated Azure DevOps connection for integration testing.

    Requires:
        - AZURE_DEVOPS_ORG environment variable
        - Appropriate Azure credentials (DefaultAzureCredential)
    """
    config = get_config()
    auth_mgr = get_auth_manager(use_default_credential=True)
    connection = auth_mgr.get_azure_devops_connection(config.azure.azure_devops_org)
    return connection


@pytest.fixture
def test_branch_name():
    """Generate a unique test branch name."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"test/integration-{timestamp}"


class TestAzureReposIntegration:
    """Integration tests for Azure Repos operations."""

    @pytest.mark.integration
    def test_create_branch_integration(self, azure_connection, test_branch_name):
        """Test creating a real branch in Azure Repos."""
        config = get_config()

        # Create a test branch
        result = create_branch(
            connection=azure_connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            branch_name=test_branch_name,
            source_branch="main",
        )

        # Verify result
        assert result["branch_name"] == test_branch_name
        assert result["source_branch"] == "main"
        assert result["success"] is True
        assert result["object_id"] is not None

    @pytest.mark.integration
    def test_commit_and_push_integration(self, azure_connection, test_branch_name):
        """Test committing and pushing files to Azure Repos."""
        config = get_config()

        # First create a branch
        create_branch(
            connection=azure_connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            branch_name=test_branch_name,
            source_branch="main",
        )

        # Commit and push files
        file_changes = {
            "test/integration_test.txt": "# Integration test file\nCreated by maf-agents integration tests",
            "test/another_file.txt": "# Another test file",
        }

        result = commit_and_push_files(
            connection=azure_connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            branch_name=test_branch_name,
            file_changes=file_changes,
            commit_message="Integration test commit",
            author_name="maf-agents-test",
            author_email="test@maf-agents.local",
        )

        # Verify result
        assert result["branch_name"] == test_branch_name
        assert result["commit_id"] is not None
        assert result["push_id"] is not None
        assert result["file_count"] == 2

    @pytest.mark.integration
    def test_create_pull_request_integration(self, azure_connection, test_branch_name):
        """Test creating a pull request in Azure Repos."""
        config = get_config()

        # First create a branch
        create_branch(
            connection=azure_connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            branch_name=test_branch_name,
            source_branch="main",
        )

        # Commit some changes
        file_changes = {
            "test/pr_test.txt": "# PR test file",
        }

        commit_and_push_files(
            connection=azure_connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            branch_name=test_branch_name,
            file_changes=file_changes,
            commit_message="Test commit for PR",
        )

        # Create pull request
        result = create_pull_request(
            connection=azure_connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            source_branch=test_branch_name,
            target_branch="main",
            title=f"[Integration Test] PR from {test_branch_name}",
            description="This is an automated integration test PR. Please close without merging.",
        )

        # Verify result
        assert result["pr_id"] is not None
        assert result["pr_url"] is not None
        assert result["source_branch"] == test_branch_name
        assert result["target_branch"] == "main"
        assert result["status"] in ["active", "notSet"]

        # Store PR ID for cleanup
        pr_id = result["pr_id"]

        # Test getting PR status
        status_result = get_pull_request_status(
            connection=azure_connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            pr_id=pr_id,
        )

        # Verify status
        assert status_result["pr_id"] == pr_id
        assert status_result["status"] in ["active", "notSet"]
        assert status_result["is_active"] is True or status_result["status"] == "notSet"
        assert status_result["title"] == f"[Integration Test] PR from {test_branch_name}"

    @pytest.mark.integration
    def test_get_pull_request_status_integration(self, azure_connection):
        """Test getting PR status for an existing PR (if any exists)."""
        config = get_config()

        # Note: This test assumes there's at least one PR in the repository
        # If no PRs exist, this test will be skipped or fail
        git_client = azure_connection.clients.get_git_client()

        # Try to get any PR
        prs = git_client.get_pull_requests(
            repository_id=config.azure.azure_devops_repo,
            project=config.azure.azure_devops_project,
        )

        if not prs:
            pytest.skip("No pull requests found in repository for testing")

        # Get status of the first PR
        pr_id = prs[0].pull_request_id
        result = get_pull_request_status(
            connection=azure_connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            pr_id=pr_id,
        )

        # Verify result has expected fields
        assert result["pr_id"] == pr_id
        assert "status" in result
        assert "is_active" in result
        assert "is_completed" in result
        assert "is_abandoned" in result
        assert "merge_status" in result
        assert "title" in result
