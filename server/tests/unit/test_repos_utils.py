"""
Unit tests for Azure Repos utility functions.

Tests Git operations (branch creation, commits, PRs) with mocked Azure DevOps SDK.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from shared.repos_utils import (
    create_branch,
    commit_and_push_files,
    create_pull_request,
    get_pull_request_status,
    fetch_recent_prs,
)


class TestCreateBranch:
    """Tests for create_branch utility function."""

    def test_create_branch_success(self):
        """Test successful branch creation."""
        # Mock connection and git client
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        # Mock get_refs to return source branch
        mock_ref = Mock()
        mock_ref.object_id = "abc123def456"
        mock_git_client.get_refs.return_value = [mock_ref]

        # Mock update_refs to return success
        mock_update_result = Mock()
        mock_update_result.success = True
        mock_git_client.update_refs.return_value = [mock_update_result]

        # Call function
        result = create_branch(
            connection=mock_connection,
            project="TestProject",
            repository_id="TestRepo",
            branch_name="feature/test-branch",
            source_branch="main",
        )

        # Verify calls
        mock_git_client.get_refs.assert_called_once()
        mock_git_client.update_refs.assert_called_once()

        # Verify result
        assert result["branch_name"] == "feature/test-branch"
        assert result["source_branch"] == "main"
        assert result["object_id"] == "abc123def456"
        assert result["success"] is True

    def test_create_branch_source_not_found(self):
        """Test branch creation when source branch doesn't exist."""
        # Mock connection and git client
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        # Mock get_refs to return empty list (branch not found)
        mock_git_client.get_refs.return_value = []

        # Call function and expect error
        with pytest.raises(ValueError, match="Source branch 'main' not found"):
            create_branch(
                connection=mock_connection,
                project="TestProject",
                repository_id="TestRepo",
                branch_name="feature/test-branch",
                source_branch="main",
            )

    def test_create_branch_with_custom_source(self):
        """Test branch creation from custom source branch."""
        # Mock connection and git client
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        # Mock get_refs
        mock_ref = Mock()
        mock_ref.object_id = "xyz789"
        mock_git_client.get_refs.return_value = [mock_ref]

        # Mock update_refs
        mock_update_result = Mock()
        mock_update_result.success = True
        mock_git_client.update_refs.return_value = [mock_update_result]

        # Call function with custom source
        result = create_branch(
            connection=mock_connection,
            project="TestProject",
            repository_id="TestRepo",
            branch_name="feature/new",
            source_branch="develop",
        )

        # Verify source branch was used
        assert result["source_branch"] == "develop"
        mock_git_client.get_refs.assert_called_once()


class TestCommitAndPushFiles:
    """Tests for commit_and_push_files utility function."""

    def test_commit_and_push_success(self):
        """Test successful commit and push."""
        # Mock connection and git client
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        # Mock get_refs to return branch
        mock_ref = Mock()
        mock_ref.object_id = "branch123"
        mock_git_client.get_refs.return_value = [mock_ref]

        # Mock create_push to return push result
        mock_commit = Mock()
        mock_commit.commit_id = "commit456"
        mock_push_result = Mock()
        mock_push_result.commits = [mock_commit]
        mock_push_result.push_id = 789
        mock_git_client.create_push.return_value = mock_push_result

        # Call function
        file_changes = {
            "detector.py": "# Detector code",
            "test_detector.py": "# Test code",
        }

        result = commit_and_push_files(
            connection=mock_connection,
            project="TestProject",
            repository_id="TestRepo",
            branch_name="feature/test",
            file_changes=file_changes,
            commit_message="Add detector",
        )

        # Verify calls
        mock_git_client.get_refs.assert_called_once()
        mock_git_client.create_push.assert_called_once()

        # Verify result
        assert result["branch_name"] == "feature/test"
        assert result["commit_id"] == "commit456"
        assert result["push_id"] == 789
        assert result["file_count"] == 2

    def test_commit_and_push_branch_not_found(self):
        """Test commit when branch doesn't exist."""
        # Mock connection and git client
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        # Mock get_refs to return empty list
        mock_git_client.get_refs.return_value = []

        # Call function and expect error
        with pytest.raises(ValueError, match="Branch 'feature/test' not found"):
            commit_and_push_files(
                connection=mock_connection,
                project="TestProject",
                repository_id="TestRepo",
                branch_name="feature/test",
                file_changes={"file.py": "content"},
                commit_message="Test commit",
            )

    def test_commit_and_push_custom_author(self):
        """Test commit with custom author details."""
        # Mock connection and git client
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        # Mock get_refs
        mock_ref = Mock()
        mock_ref.object_id = "ref123"
        mock_git_client.get_refs.return_value = [mock_ref]

        # Mock create_push
        mock_commit = Mock()
        mock_commit.commit_id = "abc"
        mock_push_result = Mock()
        mock_push_result.commits = [mock_commit]
        mock_push_result.push_id = 1
        mock_git_client.create_push.return_value = mock_push_result

        # Call function with custom author
        result = commit_and_push_files(
            connection=mock_connection,
            project="TestProject",
            repository_id="TestRepo",
            branch_name="feature/test",
            file_changes={"file.txt": "content"},
            commit_message="Custom commit",
            author_name="Test User",
            author_email="test@example.com",
        )

        # Verify push was called
        assert mock_git_client.create_push.called
        assert result["commit_id"] == "abc"


class TestCreatePullRequest:
    """Tests for create_pull_request utility function."""

    def test_create_pull_request_success(self):
        """Test successful PR creation."""
        # Mock connection and git client
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        # Mock create_pull_request to return PR result
        mock_pr_result = Mock()
        mock_pr_result.pull_request_id = 123
        mock_pr_result.url = "https://dev.azure.com/org/project/_git/repo/pullrequest/123"
        mock_pr_result.status = "active"
        mock_git_client.create_pull_request.return_value = mock_pr_result

        # Call function
        result = create_pull_request(
            connection=mock_connection,
            project="TestProject",
            repository_id="TestRepo",
            source_branch="feature/test",
            target_branch="main",
            title="Test PR",
            description="Test description",
        )

        # Verify calls
        mock_git_client.create_pull_request.assert_called_once()

        # Verify result
        assert result["pr_id"] == 123
        assert result["pr_url"] == "https://dev.azure.com/org/project/_git/repo/pullrequest/123"
        assert result["source_branch"] == "feature/test"
        assert result["target_branch"] == "main"
        assert result["title"] == "Test PR"
        assert result["status"] == "active"

    def test_create_pull_request_with_reviewers(self):
        """Test PR creation with reviewers."""
        # Mock connection and git client
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        # Mock create_pull_request
        mock_pr_result = Mock()
        mock_pr_result.pull_request_id = 456
        mock_pr_result.url = "https://dev.azure.com/org/project/_git/repo/pullrequest/456"
        mock_pr_result.status = "active"
        mock_git_client.create_pull_request.return_value = mock_pr_result

        # Call function with reviewers
        result = create_pull_request(
            connection=mock_connection,
            project="TestProject",
            repository_id="TestRepo",
            source_branch="feature/test",
            target_branch="main",
            title="Test PR with reviewers",
            description="Test",
            reviewers=["reviewer1", "reviewer2"],
        )

        # Verify PR was created
        assert result["pr_id"] == 456
        assert mock_git_client.create_pull_request.called


class TestGetPullRequestStatus:
    """Tests for get_pull_request_status utility function."""

    def test_get_pull_request_status_active(self):
        """Test getting status of an active PR."""
        # Mock connection and git client
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        # Mock get_pull_request to return PR
        mock_pr = Mock()
        mock_pr.pull_request_id = 123
        mock_pr.status = "active"
        mock_pr.merge_status = "succeeded"
        mock_pr.title = "Test PR"
        mock_pr.created_by = Mock()
        mock_pr.created_by.display_name = "Test User"
        mock_git_client.get_pull_request.return_value = mock_pr

        # Call function
        result = get_pull_request_status(
            connection=mock_connection,
            project="TestProject",
            repository_id="TestRepo",
            pr_id=123,
        )

        # Verify calls
        mock_git_client.get_pull_request.assert_called_once_with(
            pull_request_id=123,
            repository_id="TestRepo",
            project="TestProject",
        )

        # Verify result
        assert result["pr_id"] == 123
        assert result["status"] == "active"
        assert result["is_active"] is True
        assert result["is_completed"] is False
        assert result["is_abandoned"] is False
        assert result["title"] == "Test PR"

    def test_get_pull_request_status_completed(self):
        """Test getting status of a completed PR."""
        # Mock connection and git client
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        # Mock get_pull_request for completed PR
        mock_pr = Mock()
        mock_pr.pull_request_id = 456
        mock_pr.status = "completed"
        mock_pr.merge_status = "succeeded"
        mock_pr.title = "Completed PR"
        mock_pr.created_by = Mock()
        mock_pr.created_by.display_name = "Test User"
        mock_git_client.get_pull_request.return_value = mock_pr

        # Call function
        result = get_pull_request_status(
            connection=mock_connection,
            project="TestProject",
            repository_id="TestRepo",
            pr_id=456,
        )

        # Verify result
        assert result["status"] == "completed"
        assert result["is_completed"] is True
        assert result["is_active"] is False
        assert result["is_abandoned"] is False

    def test_get_pull_request_status_abandoned(self):
        """Test getting status of an abandoned PR."""
        # Mock connection and git client
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        # Mock get_pull_request for abandoned PR
        mock_pr = Mock()
        mock_pr.pull_request_id = 789
        mock_pr.status = "abandoned"
        mock_pr.merge_status = "conflicts"
        mock_pr.title = "Abandoned PR"
        mock_pr.created_by = Mock()
        mock_pr.created_by.display_name = "Test User"
        mock_git_client.get_pull_request.return_value = mock_pr

        # Call function
        result = get_pull_request_status(
            connection=mock_connection,
            project="TestProject",
            repository_id="TestRepo",
            pr_id=789,
        )

        # Verify result
        assert result["status"] == "abandoned"
        assert result["is_abandoned"] is True
        assert result["is_active"] is False
        assert result["is_completed"] is False


class TestFetchRecentPRs:
    """Tests for fetch_recent_prs utility function."""

    def test_fetch_recent_prs_success(self):
        """Test successful fetching of recent PRs."""
        # Mock connection and git client
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        # Mock PRs
        mock_pr1 = Mock()
        mock_pr1.pull_request_id = 123
        mock_pr1.title = "Add detector for rule 1"
        mock_pr1.description = "This PR adds a new detector"
        mock_pr1.created_by = Mock(display_name="Test User")
        mock_pr1.creation_date = Mock(isoformat=lambda: "2025-01-01T00:00:00")
        mock_pr1.merge_status = "succeeded"
        mock_pr1.source_ref_name = "refs/heads/feature/detector"
        mock_pr1.target_ref_name = "refs/heads/main"

        mock_pr2 = Mock()
        mock_pr2.pull_request_id = 124
        mock_pr2.title = "Update detector schema"
        mock_pr2.description = "Updates the detector schema"
        mock_pr2.created_by = Mock(display_name="Test User 2")
        mock_pr2.creation_date = Mock(isoformat=lambda: "2025-01-02T00:00:00")
        mock_pr2.merge_status = "succeeded"
        mock_pr2.source_ref_name = "refs/heads/feature/schema"
        mock_pr2.target_ref_name = "refs/heads/main"

        mock_git_client.get_pull_requests.return_value = [mock_pr1, mock_pr2]

        # Mock iterations and changes
        mock_iteration = Mock()
        mock_iteration.id = 1
        mock_git_client.get_pull_request_iterations.return_value = [mock_iteration]

        mock_change = Mock()
        mock_change.item = Mock(path="detector_rule_1.py")
        mock_change.change_type = "add"
        mock_changes = Mock()
        mock_changes.change_entries = [mock_change]
        mock_git_client.get_pull_request_iteration_changes.return_value = mock_changes

        # Call function
        result = fetch_recent_prs(
            connection=mock_connection,
            project="TestProject",
            repository_id="TestRepo",
            limit=10,
        )

        # Verify results
        assert len(result) == 2
        assert result[0]["pr_id"] == 123
        assert result[0]["title"] == "Add detector for rule 1"
        assert len(result[0]["files"]) == 1
        assert result[0]["files"][0]["path"] == "detector_rule_1.py"

    def test_fetch_recent_prs_with_filter(self):
        """Test fetching PRs with detector-only filter."""
        # Mock connection and git client
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        # Mock PRs - one detector-related, one not
        mock_pr_detector = Mock()
        mock_pr_detector.pull_request_id = 123
        mock_pr_detector.title = "Add detector for rule 1"
        mock_pr_detector.description = "Detector PR"
        mock_pr_detector.created_by = Mock(display_name="User")
        mock_pr_detector.creation_date = Mock(isoformat=lambda: "2025-01-01T00:00:00")
        mock_pr_detector.merge_status = "succeeded"
        mock_pr_detector.source_ref_name = "refs/heads/feature"
        mock_pr_detector.target_ref_name = "refs/heads/main"

        mock_pr_other = Mock()
        mock_pr_other.pull_request_id = 124
        mock_pr_other.title = "Fix typo in README"
        mock_pr_other.description = "Documentation fix"
        mock_pr_other.created_by = Mock(display_name="User")
        mock_pr_other.creation_date = Mock(isoformat=lambda: "2025-01-02T00:00:00")
        mock_pr_other.merge_status = "succeeded"
        mock_pr_other.source_ref_name = "refs/heads/docs"
        mock_pr_other.target_ref_name = "refs/heads/main"

        mock_git_client.get_pull_requests.return_value = [mock_pr_detector, mock_pr_other]

        # Mock empty iterations
        mock_git_client.get_pull_request_iterations.return_value = []

        # Call function with filter
        result = fetch_recent_prs(
            connection=mock_connection,
            project="TestProject",
            repository_id="TestRepo",
            limit=10,
            include_detector_only=True,
        )

        # Should only include detector PR
        assert len(result) == 1
        assert result[0]["pr_id"] == 123

    def test_fetch_recent_prs_no_files(self):
        """Test fetching PRs when file retrieval fails."""
        # Mock connection and git client
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        # Mock PR
        mock_pr = Mock()
        mock_pr.pull_request_id = 123
        mock_pr.title = "Add detector"
        mock_pr.description = "Test"
        mock_pr.created_by = Mock(display_name="User")
        mock_pr.creation_date = Mock(isoformat=lambda: "2025-01-01T00:00:00")
        mock_pr.merge_status = "succeeded"
        mock_pr.source_ref_name = "refs/heads/feature"
        mock_pr.target_ref_name = "refs/heads/main"

        mock_git_client.get_pull_requests.return_value = [mock_pr]

        # Mock iterations to raise exception
        mock_git_client.get_pull_request_iterations.side_effect = Exception("API Error")

        # Call function
        result = fetch_recent_prs(
            connection=mock_connection,
            project="TestProject",
            repository_id="TestRepo",
        )

        # Should still return PR but with empty files
        assert len(result) == 1
        assert result[0]["pr_id"] == 123
        assert result[0]["files"] == []
