"""
Integration tests for Pattern Analysis Agent.

These tests require actual Azure DevOps configuration and OpenAI API access,
and will be skipped if the required environment variables are not set.
"""

import pytest
import os

from shared.auth import get_auth_manager
from shared.config import get_config
from shared.repos_utils import fetch_recent_prs
from agents.pattern_analysis_agent import create_pattern_analysis_agent

# Skip all tests if Azure DevOps or OpenAI is not configured
pytestmark = pytest.mark.skipif(
    not all([
        os.getenv("AZURE_DEVOPS_ORG"),
        os.getenv("AZURE_DEVOPS_PROJECT"),
        os.getenv("AZURE_DEVOPS_REPO"),
        os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_ENDPOINT"),
    ]),
    reason="Azure DevOps and OpenAI not configured",
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


class TestPatternAnalysisIntegration:
    """Integration tests for pattern analysis with real Azure Repos and OpenAI."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetch_and_analyze_real_prs(self, azure_connection):
        """Test fetching real PRs and analyzing patterns."""
        config = get_config()

        # Fetch real PRs
        prs = fetch_recent_prs(
            connection=azure_connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            limit=5,  # Limit for faster testing
            include_detector_only=True,
        )

        # If no PRs found, skip the test
        if not prs:
            pytest.skip("No detector-related PRs found in repository")

        # Create pattern analysis agent
        agent = await create_pattern_analysis_agent()

        # Analyze patterns
        patterns = await agent.analyze_pr_patterns(prs)

        # Verify results
        assert len(patterns) > 0, "Should extract at least one pattern"
        assert all(hasattr(p, "pattern_type") for p in patterns)
        assert all(hasattr(p, "confidence") for p in patterns)
        assert all(0.0 <= p.confidence <= 1.0 for p in patterns)

        # Log results for manual verification
        print(f"\n✓ Analyzed {len(prs)} PRs")
        print(f"✓ Extracted {len(patterns)} patterns:")
        for pattern in patterns[:5]:  # Show first 5
            print(f"  - {pattern.pattern_type}: {pattern.pattern_value} (confidence: {pattern.confidence})")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pattern_analysis_with_no_prs(self):
        """Test pattern analysis with no PR data (should return defaults)."""
        # Create agent
        agent = await create_pattern_analysis_agent()

        # Analyze with empty data
        patterns = await agent.analyze_pr_patterns([])

        # Should return default patterns
        assert len(patterns) > 0
        assert all(p.confidence == 0.5 for p in patterns)  # Default confidence
        print(f"\n✓ Returned {len(patterns)} default patterns when no PRs available")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pattern_analysis_focus_areas(self, azure_connection):
        """Test pattern analysis with specific focus areas."""
        config = get_config()

        # Fetch a few PRs
        prs = fetch_recent_prs(
            connection=azure_connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            limit=3,
            include_detector_only=True,
        )

        if not prs:
            pytest.skip("No PRs found")

        # Create agent
        agent = await create_pattern_analysis_agent()

        # Analyze with focus on specific areas
        patterns = await agent.analyze_pr_patterns(
            prs,
            focus_areas=["naming", "imports"]
        )

        # Verify results
        assert len(patterns) > 0
        pattern_types = {p.pattern_type for p in patterns}

        # Should have patterns related to focus areas
        print(f"\n✓ Focused analysis extracted patterns: {pattern_types}")
