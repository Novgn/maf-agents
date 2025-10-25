"""
Unit tests for Production Promotion Pattern Analyzer.

Tests pattern extraction from historical production promotion PRs.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from agents.promotion_pattern_analyzer import (
    PromotionPatternAnalyzer,
    create_promotion_pattern_analyzer
)


def create_mock_pr(
    pr_id: int,
    title: str,
    description: str = "",
    files: list = None
) -> dict:
    """Helper to create mock PR data."""
    return {
        "pullRequestId": pr_id,
        "title": title,
        "description": description,
        "creationDate": f"2024-01-{pr_id:02d}T12:00:00Z",
        "url": f"https://dev.azure.com/test/project/_git/repo/pullrequest/{pr_id}",
        "createdBy": {"displayName": f"User{pr_id}"},
        "commits": [
            {
                "changes": [
                    {"item": {"path": file_path}}
                    for file_path in (files or [])
                ]
            }
        ]
    }


class TestPromotionPatternAnalyzerInitialization:
    """Tests for PromotionPatternAnalyzer initialization."""

    def test_init(self):
        """Test analyzer initialization."""
        mock_connection = Mock()
        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        assert analyzer.connection == mock_connection
        assert analyzer.project == "test-project"
        assert analyzer.repository == "test-repo"

    def test_create_factory(self):
        """Test factory function."""
        mock_connection = Mock()
        analyzer = create_promotion_pattern_analyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        assert isinstance(analyzer, PromotionPatternAnalyzer)
        assert analyzer.project == "test-project"


class TestFetchPromotionPRs:
    """Tests for fetch_promotion_prs method."""

    def test_fetch_promotion_prs_success(self):
        """Test successful fetching of promotion PRs."""
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        # Mock PR objects
        mock_pr1 = Mock()
        mock_pr1.pull_request_id = 1
        mock_pr1.title = "Promote detector to production"
        mock_pr1.description = "Production deployment"
        mock_pr1.creation_date = None
        mock_pr1.url = "https://dev.azure.com/test/project/_git/repo/pullrequest/1"
        mock_pr1.created_by.display_name = "User1"

        mock_pr2 = Mock()
        mock_pr2.pull_request_id = 2
        mock_pr2.title = "Enable customer-facing feature"
        mock_pr2.description = ""
        mock_pr2.creation_date = None
        mock_pr2.url = "https://dev.azure.com/test/project/_git/repo/pullrequest/2"
        mock_pr2.created_by.display_name = "User2"

        mock_git_client.get_pull_requests.return_value = [mock_pr1, mock_pr2]
        mock_git_client.get_pull_request_iterations.return_value = []

        prs = analyzer.fetch_promotion_prs(limit=10)

        # Verify results
        assert len(prs) == 2
        assert prs[0]["pullRequestId"] == 1
        assert prs[0]["title"] == "Promote detector to production"
        assert prs[1]["pullRequestId"] == 2

    def test_fetch_promotion_prs_with_limit(self):
        """Test fetching PRs with limit."""
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        # Mock many PRs
        mock_prs = []
        for i in range(1, 11):
            mock_pr = Mock()
            mock_pr.pull_request_id = i
            mock_pr.title = f"Production change {i}"
            mock_pr.description = ""
            mock_pr.creation_date = None
            mock_pr.url = f"https://dev.azure.com/test/project/_git/repo/pullrequest/{i}"
            mock_pr.created_by.display_name = f"User{i}"
            mock_prs.append(mock_pr)

        mock_git_client.get_pull_requests.return_value = mock_prs
        mock_git_client.get_pull_request_iterations.return_value = []

        prs = analyzer.fetch_promotion_prs(limit=5)

        # Verify limit applied
        assert len(prs) == 5

    def test_fetch_promotion_prs_search_error(self):
        """Test handling search errors gracefully."""
        mock_connection = Mock()
        mock_git_client = Mock()
        mock_connection.clients.get_git_client.return_value = mock_git_client

        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        # Mock search failure
        mock_git_client.get_pull_requests.side_effect = Exception("API error")

        prs = analyzer.fetch_promotion_prs(limit=10)

        # Should return empty list on error
        assert prs == []


class TestExtractPromotionPatterns:
    """Tests for extract_promotion_patterns method."""

    def test_extract_patterns_from_prs(self):
        """Test pattern extraction from mock PRs."""
        mock_connection = Mock()
        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        # Mock PRs with various patterns
        mock_prs = [
            create_mock_pr(
                1,
                "Promote: Enable detector feature",
                "## Summary\nEnable production detector\n## Testing\nTested in staging",
                ["/config/features.json", "/docs/README.md"]
            ),
            create_mock_pr(
                2,
                "Production: Customer-facing update",
                "## Summary\nUpdate customer config\n## Testing\nValidated",
                ["/config/production.yaml", "/flags/detector_flag.json"]
            ),
            create_mock_pr(
                3,
                "Promote: Feature flag update",
                "## Summary\nEnable feature flag",
                ["/config/app.json", "/flags/features.json"]
            ),
        ]

        patterns = analyzer.extract_promotion_patterns(mock_prs)

        # Verify pattern structure
        assert "file_patterns" in patterns
        assert "title_patterns" in patterns
        assert "description_patterns" in patterns
        assert "production_indicators" in patterns
        assert "pr_count" in patterns
        assert "examples" in patterns

        # Verify PR count
        assert patterns["pr_count"] == 3

        # Verify examples
        assert len(patterns["examples"]) == 3

    def test_extract_patterns_empty_prs(self):
        """Test pattern extraction with no PRs."""
        mock_connection = Mock()
        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        patterns = analyzer.extract_promotion_patterns([])

        # Should return default patterns
        assert patterns["pr_count"] == 0
        assert patterns["file_patterns"] is not None
        assert patterns["title_patterns"] is not None

    def test_extract_patterns_identifies_feature_flags(self):
        """Test identification of feature flag files."""
        mock_connection = Mock()
        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        mock_prs = [
            create_mock_pr(
                1,
                "Enable feature",
                "",
                ["/flags/detector_feature.json", "/flags/production_flags.yaml"]
            ),
        ]

        patterns = analyzer.extract_promotion_patterns(mock_prs)

        # Check production indicators
        indicators = patterns["production_indicators"]
        feature_flag_indicators = [i for i in indicators if i["type"] == "feature_flags"]
        assert len(feature_flag_indicators) > 0
        assert feature_flag_indicators[0]["count"] == 2

    def test_extract_patterns_identifies_config_files(self):
        """Test identification of configuration files."""
        mock_connection = Mock()
        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        mock_prs = [
            create_mock_pr(
                1,
                "Update config",
                "",
                ["/config/production.json", "/config/app.yaml", "/settings/env.yml"]
            ),
        ]

        patterns = analyzer.extract_promotion_patterns(mock_prs)

        # Check production indicators
        indicators = patterns["production_indicators"]
        config_indicators = [i for i in indicators if i["type"] == "configuration"]
        assert len(config_indicators) > 0
        assert config_indicators[0]["count"] == 3


class TestAnalyzeFilePatterns:
    """Tests for _analyze_file_patterns method."""

    def test_analyze_file_extensions(self):
        """Test analysis of file extensions."""
        mock_connection = Mock()
        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        files = [
            "/config/app.json",
            "/config/features.json",
            "/docs/README.md",
            "/flags/feature.yaml",
            "/flags/prod.yaml",
        ]

        patterns = analyzer._analyze_file_patterns(files)

        # Should identify common extensions
        extensions = [p for p in patterns if p["type"] == "file_extension"]
        assert len(extensions) > 0

        # JSON and YAML should be common
        ext_values = [p["value"] for p in extensions]
        assert ".json" in ext_values or ".yaml" in ext_values

    def test_analyze_common_directories(self):
        """Test analysis of common directories."""
        mock_connection = Mock()
        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        files = [
            "/config/app.json",
            "/config/prod.json",
            "/config/features.json",
            "/flags/detector.yaml",
        ]

        patterns = analyzer._analyze_file_patterns(files)

        # Should identify /config as common directory
        directories = [p for p in patterns if p["type"] == "directory"]
        assert len(directories) > 0
        assert any("/config" in p["value"] for p in directories)

    def test_analyze_empty_files(self):
        """Test analysis with no files."""
        mock_connection = Mock()
        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        patterns = analyzer._analyze_file_patterns([])

        assert patterns == []


class TestAnalyzeTitlePatterns:
    """Tests for _analyze_title_patterns method."""

    def test_analyze_title_prefixes(self):
        """Test extraction of title prefixes."""
        mock_connection = Mock()
        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        titles = [
            "Promote: Enable detector feature",
            "Promote: Update configuration",
            "Production: Customer-facing update",
        ]

        patterns = analyzer._analyze_title_patterns(titles)

        # Should identify "Promote" as common prefix
        prefixes = [p for p in patterns if p["type"] == "title_prefix"]
        assert len(prefixes) > 0
        assert any(p["value"] == "Promote" for p in prefixes)

    def test_analyze_title_keywords(self):
        """Test identification of common keywords."""
        mock_connection = Mock()
        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        titles = [
            "Enable production feature",
            "Promote to customer-facing",
            "Production flag update",
        ]

        patterns = analyzer._analyze_title_patterns(titles)

        # Should identify "production" keyword
        keywords = [p for p in patterns if p["type"] == "title_keyword"]
        assert len(keywords) > 0
        assert any(p["value"] == "production" for p in keywords)


class TestAnalyzeDescriptionPatterns:
    """Tests for _analyze_description_patterns method."""

    def test_analyze_markdown_sections(self):
        """Test extraction of markdown section headers."""
        mock_connection = Mock()
        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        descriptions = [
            "## Summary\nDescription\n## Testing\nTest plan",
            "## Summary\nAnother description\n## Changes\nFile list",
            "## Summary\nYet another\n## Testing\nTests",
        ]

        patterns = analyzer._analyze_description_patterns(descriptions)

        # Should identify "Summary" and "Testing" as common sections
        sections = [p for p in patterns if p["type"] == "description_section"]
        assert len(sections) > 0
        assert any(p["value"] == "Summary" for p in sections)


class TestIdentifyProductionIndicators:
    """Tests for _identify_production_indicators method."""

    def test_identify_feature_flags(self):
        """Test identification of feature flag files."""
        mock_connection = Mock()
        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        files = [
            "/flags/detector_feature.json",
            "/config/feature_flags.yaml",
            "/app/features/flag_config.json",
        ]

        indicators = analyzer._identify_production_indicators(files)

        # Should identify feature flags
        flag_indicators = [i for i in indicators if i["type"] == "feature_flags"]
        assert len(flag_indicators) > 0
        assert flag_indicators[0]["count"] >= 2

    def test_identify_config_files(self):
        """Test identification of configuration files."""
        mock_connection = Mock()
        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        files = [
            "/config/production.json",
            "/config/app.yaml",
            "/settings/config.yml",
        ]

        indicators = analyzer._identify_production_indicators(files)

        # Should identify config files
        config_indicators = [i for i in indicators if i["type"] == "configuration"]
        assert len(config_indicators) > 0
        assert config_indicators[0]["count"] == 3

    def test_identify_documentation(self):
        """Test identification of documentation files."""
        mock_connection = Mock()
        analyzer = PromotionPatternAnalyzer(
            connection=mock_connection,
            project="test-project",
            repository="test-repo"
        )

        files = [
            "/README.md",
            "/docs/setup.md",
            "/documentation/guide.md",
        ]

        indicators = analyzer._identify_production_indicators(files)

        # Should identify documentation
        doc_indicators = [i for i in indicators if i["type"] == "documentation"]
        assert len(doc_indicators) > 0
        assert doc_indicators[0]["count"] == 3
