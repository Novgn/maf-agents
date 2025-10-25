"""
Production Promotion Pattern Analyzer.

This module analyzes historical production promotion PRs to extract
patterns and conventions for creating new promotion PRs.
"""

from typing import Dict, Any, List, Optional
import re
from collections import Counter

import structlog

logger = structlog.get_logger(__name__)


class PromotionPatternAnalyzer:
    """
    Analyzes historical production promotion PRs to identify patterns.

    This analyzer helps ensure new promotion PRs follow established
    conventions for feature flags, config changes, and documentation.
    """

    def __init__(self, connection, project: str, repository: str):
        """
        Initialize the Promotion Pattern Analyzer.

        Args:
            connection: Azure DevOps connection from AuthenticationManager
            project: Azure DevOps project name
            repository: Repository name
        """
        self.connection = connection
        self.project = project
        self.repository = repository
        self.logger = logger.bind(
            project=project,
            repository=repository,
            analyzer="promotion_pattern"
        )

    def fetch_promotion_prs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch recent production promotion PRs from Azure Repos.

        Searches for PRs with keywords like "production", "customer-facing",
        "promote", etc. in their titles or descriptions.

        Args:
            limit: Maximum number of PRs to fetch (default: 10)

        Returns:
            List of PR dictionaries with details and file changes
        """
        self.logger.info("Fetching production promotion PRs", limit=limit)

        git_client = self.connection.clients.get_git_client()

        try:
            # Get completed (merged) PRs
            prs = git_client.get_pull_requests(
                repository_id=self.repository,
                project=self.project,
                search_criteria={
                    "status": "completed",  # Only merged PRs
                    "includeLinks": True,
                },
            )

            # Promotion keywords to filter PRs
            promotion_keywords = ["production", "customer-facing", "promote", "prod", "enable"]

            # Filter PRs by promotion keywords in title or description
            promotion_prs = []
            for pr in prs:
                title_lower = (pr.title or "").lower()
                description_lower = (pr.description or "").lower()

                if any(keyword in title_lower or keyword in description_lower
                       for keyword in promotion_keywords):
                    # Get PR changes/files
                    try:
                        iterations = git_client.get_pull_request_iterations(
                            pull_request_id=pr.pull_request_id,
                            repository_id=self.repository,
                            project=self.project,
                        )

                        # Get files from the latest iteration
                        files = []
                        if iterations:
                            latest_iteration = iterations[-1]
                            changes = git_client.get_pull_request_iteration_changes(
                                pull_request_id=pr.pull_request_id,
                                iteration_id=latest_iteration.id,
                                repository_id=self.repository,
                                project=self.project,
                            )

                            for change in changes.change_entries:
                                if change.item and hasattr(change.item, 'path'):
                                    files.append(change.item.path)

                        # Convert to dictionary format
                        pr_dict = {
                            "pullRequestId": pr.pull_request_id,
                            "title": pr.title,
                            "description": pr.description or "",
                            "creationDate": pr.creation_date.isoformat() if pr.creation_date else "",
                            "url": pr.url,
                            "createdBy": {
                                "displayName": pr.created_by.display_name if pr.created_by else "Unknown"
                            },
                            "commits": [
                                {
                                    "changes": [
                                        {"item": {"path": file_path}}
                                        for file_path in files
                                    ]
                                }
                            ]
                        }

                        promotion_prs.append(pr_dict)

                        # Stop if we've reached the limit
                        if len(promotion_prs) >= limit:
                            break

                    except Exception as e:
                        self.logger.warning(
                            "Error fetching PR details",
                            pr_id=pr.pull_request_id,
                            error=str(e)
                        )
                        continue

            self.logger.info(
                "Fetched promotion PRs",
                total_found=len(promotion_prs),
                returned=min(len(promotion_prs), limit)
            )

            return promotion_prs[:limit]

        except Exception as e:
            self.logger.error(
                "Error fetching promotion PRs",
                error=str(e)
            )
            return []

    def extract_promotion_patterns(
        self,
        prs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract common patterns from production promotion PRs.

        Analyzes file changes, commit messages, and PR descriptions to
        identify patterns like:
        - Feature flag files
        - Configuration files
        - Documentation updates
        - Naming conventions
        - Common file paths

        Args:
            prs: List of PR dictionaries from fetch_promotion_prs()

        Returns:
            Dictionary with extracted patterns and examples
        """
        if not prs:
            self.logger.warning("No PRs provided for pattern extraction")
            return self._get_default_patterns()

        self.logger.info("Extracting patterns from PRs", pr_count=len(prs))

        # Collect all file paths from PRs
        all_files = []
        all_titles = []
        all_descriptions = []

        for pr in prs:
            # Extract title and description
            all_titles.append(pr.get("title", ""))
            all_descriptions.append(pr.get("description", ""))

            # Extract file paths from commits or file changes
            # Note: Detailed file info may require additional API calls
            commits = pr.get("commits", [])
            for commit in commits:
                # Extract files from commit (if available)
                changes = commit.get("changes", [])
                for change in changes:
                    item = change.get("item", {})
                    path = item.get("path", "")
                    if path:
                        all_files.append(path)

        # Analyze file patterns
        file_patterns = self._analyze_file_patterns(all_files)

        # Analyze title patterns
        title_patterns = self._analyze_title_patterns(all_titles)

        # Analyze description patterns
        description_patterns = self._analyze_description_patterns(all_descriptions)

        # Identify production-readiness indicators
        production_indicators = self._identify_production_indicators(all_files)

        patterns = {
            "file_patterns": file_patterns,
            "title_patterns": title_patterns,
            "description_patterns": description_patterns,
            "production_indicators": production_indicators,
            "pr_count": len(prs),
            "examples": self._extract_examples(prs[:3]),  # Top 3 PRs as examples
        }

        self.logger.info(
            "Pattern extraction complete",
            file_patterns_count=len(file_patterns),
            production_indicators_count=len(production_indicators)
        )

        return patterns

    def _analyze_file_patterns(self, files: List[str]) -> List[Dict[str, Any]]:
        """Analyze file paths to identify common patterns."""
        if not files:
            return []

        # Count file extensions
        extensions = Counter()
        directories = Counter()
        filenames = Counter()

        for file_path in files:
            # Extract extension
            if "." in file_path:
                ext = file_path.split(".")[-1]
                extensions[ext] += 1

            # Extract directory
            if "/" in file_path:
                directory = "/".join(file_path.split("/")[:-1])
                directories[directory] += 1

            # Extract filename
            filename = file_path.split("/")[-1]
            filenames[filename] += 1

        patterns = []

        # Most common extensions
        for ext, count in extensions.most_common(5):
            patterns.append({
                "type": "file_extension",
                "value": f".{ext}",
                "count": count,
                "confidence": count / len(files) if files else 0
            })

        # Most common directories
        for directory, count in directories.most_common(5):
            patterns.append({
                "type": "directory",
                "value": directory,
                "count": count,
                "confidence": count / len(files) if files else 0
            })

        return patterns

    def _analyze_title_patterns(self, titles: List[str]) -> List[Dict[str, Any]]:
        """Analyze PR titles to identify naming conventions."""
        if not titles:
            return []

        patterns = []

        # Common prefix patterns
        prefix_counts = Counter()
        for title in titles:
            # Extract first word or phrase before colon/hyphen
            match = re.match(r"^([A-Za-z]+(?:\s+[A-Za-z]+)?)[:\-]", title)
            if match:
                prefix = match.group(1).strip()
                prefix_counts[prefix] += 1

        for prefix, count in prefix_counts.most_common(3):
            patterns.append({
                "type": "title_prefix",
                "value": prefix,
                "count": count,
                "confidence": count / len(titles) if titles else 0
            })

        # Common keywords in titles
        keywords = ["promote", "production", "customer-facing", "enable", "feature", "flag"]
        for keyword in keywords:
            count = sum(1 for title in titles if keyword.lower() in title.lower())
            if count > 0:
                patterns.append({
                    "type": "title_keyword",
                    "value": keyword,
                    "count": count,
                    "confidence": count / len(titles) if titles else 0
                })

        return patterns

    def _analyze_description_patterns(
        self,
        descriptions: List[str]
    ) -> List[Dict[str, Any]]:
        """Analyze PR descriptions to identify common sections."""
        if not descriptions:
            return []

        patterns = []

        # Common section headers (e.g., ## Summary, ## Testing)
        section_headers = Counter()
        for description in descriptions:
            # Find markdown headers
            headers = re.findall(r"^#{1,3}\s+(.+)$", description, re.MULTILINE)
            for header in headers:
                section_headers[header.strip()] += 1

        for header, count in section_headers.most_common(5):
            patterns.append({
                "type": "description_section",
                "value": header,
                "count": count,
                "confidence": count / len(descriptions) if descriptions else 0
            })

        return patterns

    def _identify_production_indicators(
        self,
        files: List[str]
    ) -> List[Dict[str, Any]]:
        """Identify file patterns that indicate production readiness."""
        if not files:
            return []

        indicators = []

        # Feature flag patterns
        flag_files = [f for f in files if "flag" in f.lower() or "feature" in f.lower()]
        if flag_files:
            indicators.append({
                "type": "feature_flags",
                "description": "Feature flag configuration files",
                "count": len(flag_files),
                "examples": flag_files[:3]
            })

        # Configuration file patterns
        config_files = [f for f in files if "config" in f.lower() or ".json" in f or ".yaml" in f or ".yml" in f]
        if config_files:
            indicators.append({
                "type": "configuration",
                "description": "Configuration files",
                "count": len(config_files),
                "examples": config_files[:3]
            })

        # Documentation patterns
        doc_files = [f for f in files if "readme" in f.lower() or "doc" in f.lower() or ".md" in f.lower()]
        if doc_files:
            indicators.append({
                "type": "documentation",
                "description": "Documentation files",
                "count": len(doc_files),
                "examples": doc_files[:3]
            })

        return indicators

    def _extract_examples(self, prs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract example PRs for reference."""
        examples = []

        for pr in prs:
            examples.append({
                "pr_id": pr.get("pullRequestId"),
                "title": pr.get("title", ""),
                "description": pr.get("description", "")[:200],  # First 200 chars
                "url": pr.get("url", ""),
                "created_by": pr.get("createdBy", {}).get("displayName", "Unknown"),
                "creation_date": pr.get("creationDate", ""),
            })

        return examples

    def _get_default_patterns(self) -> Dict[str, Any]:
        """Return default patterns when no PRs are available."""
        return {
            "file_patterns": [
                {
                    "type": "file_extension",
                    "value": ".json",
                    "count": 0,
                    "confidence": 0.0
                }
            ],
            "title_patterns": [
                {
                    "type": "title_prefix",
                    "value": "Promote",
                    "count": 0,
                    "confidence": 0.0
                }
            ],
            "description_patterns": [],
            "production_indicators": [],
            "pr_count": 0,
            "examples": []
        }


def create_promotion_pattern_analyzer(
    connection,
    project: str,
    repository: str
) -> PromotionPatternAnalyzer:
    """
    Factory function to create a PromotionPatternAnalyzer.

    Args:
        connection: Azure DevOps connection
        project: Azure DevOps project name
        repository: Repository name

    Returns:
        Configured PromotionPatternAnalyzer instance
    """
    return PromotionPatternAnalyzer(connection, project, repository)
