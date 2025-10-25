"""
Azure Repos utility functions for Git operations.

These are simple utility functions that use the Azure DevOps Python SDK directly.
Following MAF best practices: NO wrapper classes, just utility functions.
"""

from typing import Dict, Any, Optional
from azure.devops.connection import Connection
from azure.devops.v7_1.git.models import (
    GitRefUpdate,
    GitPush,
    GitPullRequest,
)
import structlog

logger = structlog.get_logger(__name__)


def create_branch(
    connection: Connection,
    project: str,
    repository_id: str,
    branch_name: str,
    source_branch: str = "main",
) -> Dict[str, Any]:
    """
    Create a new Git branch in Azure Repos.

    Args:
        connection: Authenticated Azure DevOps connection
        project: Project name
        repository_id: Repository ID or name
        branch_name: Name of the new branch (without 'refs/heads/')
        source_branch: Source branch to branch from (default: 'main')

    Returns:
        Dictionary with branch details

    Raises:
        Exception: If branch creation fails
    """
    git_client = connection.clients.get_git_client()

    try:
        # Get the source branch ref to get its object ID
        source_ref = f"refs/heads/{source_branch}"
        refs = git_client.get_refs(
            repository_id=repository_id,
            project=project,
            filter=source_ref,
        )

        if not refs or len(refs) == 0:
            raise ValueError(f"Source branch '{source_branch}' not found")

        source_object_id = refs[0].object_id

        # Create the new branch ref
        new_ref = GitRefUpdate(
            name=f"refs/heads/{branch_name}",
            old_object_id="0000000000000000000000000000000000000000",  # Create new ref
            new_object_id=source_object_id,
        )

        # Update refs to create the branch
        result = git_client.update_refs(
            ref_updates=[new_ref],
            repository_id=repository_id,
            project=project,
        )

        logger.info(
            "Created branch in Azure Repos",
            project=project,
            repository=repository_id,
            branch=branch_name,
            source_branch=source_branch,
        )

        return {
            "branch_name": branch_name,
            "source_branch": source_branch,
            "object_id": source_object_id,
            "success": result[0].success if result else False,
        }

    except Exception as e:
        logger.error(
            "Failed to create branch",
            project=project,
            repository=repository_id,
            branch=branch_name,
            error=str(e),
        )
        raise


def commit_and_push_files(
    connection: Connection,
    project: str,
    repository_id: str,
    branch_name: str,
    file_changes: Dict[str, str],
    commit_message: str,
    author_name: str = "maf-agents",
    author_email: str = "maf-agents@microsoft.com",
) -> Dict[str, Any]:
    """
    Commit and push files to a branch in Azure Repos.

    Args:
        connection: Authenticated Azure DevOps connection
        project: Project name
        repository_id: Repository ID or name
        branch_name: Target branch name (without 'refs/heads/')
        file_changes: Dictionary mapping file paths to content
        commit_message: Commit message
        author_name: Author name for the commit
        author_email: Author email for the commit

    Returns:
        Dictionary with commit details

    Raises:
        Exception: If commit/push fails
    """
    git_client = connection.clients.get_git_client()

    try:
        # Get the branch ref to get its current object ID
        branch_ref = f"refs/heads/{branch_name}"
        refs = git_client.get_refs(
            repository_id=repository_id,
            project=project,
            filter=branch_ref,
        )

        if not refs or len(refs) == 0:
            raise ValueError(f"Branch '{branch_name}' not found")

        old_object_id = refs[0].object_id

        # Create changes for each file
        # Using dictionary structure instead of model classes for compatibility
        changes = []
        for file_path, content in file_changes.items():
            change = {
                "changeType": "add",  # 1 = add
                "item": {"path": file_path},
                "newContent": {
                    "content": content,
                    "contentType": "rawtext",
                },
            }
            changes.append(change)

        # Create commit dictionary
        commit = {
            "comment": commit_message,
            "changes": changes,
            "author": {
                "name": author_name,
                "email": author_email,
            },
        }

        # Create push with the commit
        push = GitPush(
            ref_updates=[
                GitRefUpdate(
                    name=branch_ref,
                    old_object_id=old_object_id,
                )
            ],
            commits=[commit],
        )

        # Push the changes
        result = git_client.create_push(
            push=push,
            repository_id=repository_id,
            project=project,
        )

        logger.info(
            "Committed and pushed files to Azure Repos",
            project=project,
            repository=repository_id,
            branch=branch_name,
            file_count=len(file_changes),
            commit_id=result.commits[0].commit_id if result.commits else None,
        )

        return {
            "branch_name": branch_name,
            "commit_id": result.commits[0].commit_id if result.commits else None,
            "push_id": result.push_id,
            "file_count": len(file_changes),
        }

    except Exception as e:
        logger.error(
            "Failed to commit and push files",
            project=project,
            repository=repository_id,
            branch=branch_name,
            error=str(e),
        )
        raise


def create_pull_request(
    connection: Connection,
    project: str,
    repository_id: str,
    source_branch: str,
    target_branch: str,
    title: str,
    description: str,
    reviewers: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Create a pull request in Azure Repos.

    Args:
        connection: Authenticated Azure DevOps connection
        project: Project name
        repository_id: Repository ID or name
        source_branch: Source branch name (without 'refs/heads/')
        target_branch: Target branch name (without 'refs/heads/')
        title: PR title
        description: PR description
        reviewers: Optional list of reviewer IDs

    Returns:
        Dictionary with PR details including PR ID and URL

    Raises:
        Exception: If PR creation fails
    """
    git_client = connection.clients.get_git_client()

    try:
        # Create pull request object
        pr = GitPullRequest(
            source_ref_name=f"refs/heads/{source_branch}",
            target_ref_name=f"refs/heads/{target_branch}",
            title=title,
            description=description,
        )

        # Add reviewers if provided
        if reviewers:
            pr.reviewers = [{"id": reviewer_id} for reviewer_id in reviewers]

        # Create the PR
        result = git_client.create_pull_request(
            git_pull_request_to_create=pr,
            repository_id=repository_id,
            project=project,
        )

        logger.info(
            "Created pull request in Azure Repos",
            project=project,
            repository=repository_id,
            pr_id=result.pull_request_id,
            source_branch=source_branch,
            target_branch=target_branch,
        )

        return {
            "pr_id": result.pull_request_id,
            "pr_url": result.url,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "status": result.status,
        }

    except Exception as e:
        logger.error(
            "Failed to create pull request",
            project=project,
            repository=repository_id,
            source_branch=source_branch,
            target_branch=target_branch,
            error=str(e),
        )
        raise


def get_pull_request_status(
    connection: Connection,
    project: str,
    repository_id: str,
    pr_id: int,
) -> Dict[str, Any]:
    """
    Get the status of a pull request in Azure Repos.

    Args:
        connection: Authenticated Azure DevOps connection
        project: Project name
        repository_id: Repository ID or name
        pr_id: Pull request ID

    Returns:
        Dictionary with PR status information

    Raises:
        Exception: If fetching PR status fails
    """
    git_client = connection.clients.get_git_client()

    try:
        # Get the PR
        pr = git_client.get_pull_request(
            pull_request_id=pr_id,
            repository_id=repository_id,
            project=project,
        )

        # Map status to boolean for convenience
        # Status values: "active", "completed", "abandoned", "notSet"
        is_completed = pr.status == "completed"
        is_active = pr.status == "active"
        is_abandoned = pr.status == "abandoned"

        logger.info(
            "Retrieved pull request status",
            project=project,
            repository=repository_id,
            pr_id=pr_id,
            status=pr.status,
        )

        return {
            "pr_id": pr_id,
            "status": pr.status,
            "is_completed": is_completed,
            "is_active": is_active,
            "is_abandoned": is_abandoned,
            "merge_status": pr.merge_status,
            "title": pr.title,
            "created_by": pr.created_by.display_name if pr.created_by else None,
        }

    except Exception as e:
        logger.error(
            "Failed to get pull request status",
            project=project,
            repository=repository_id,
            pr_id=pr_id,
            error=str(e),
        )
        raise
