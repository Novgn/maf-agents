"""
Pattern Analysis Agent using Microsoft Agent Framework.

This module implements an agent that analyzes historical PRs to extract
naming conventions and code patterns using LLM intelligence.
"""

from typing import Optional, Dict, Any, List
import re
import json

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient

from shared.models import CodePattern
import structlog

logger = structlog.get_logger(__name__)


class PatternAnalysisAgent:
    """
    Pattern Analysis Agent using Microsoft Agent Framework.

    This agent uses LLM intelligence (ChatAgent) to analyze historical PRs
    and extract naming conventions and code patterns.
    """

    def __init__(self):
        """
        Initialize the Pattern Analysis Agent.

        Uses Azure OpenAI for LLM-based pattern analysis.
        """
        # Create the chat client
        chat_client = AzureOpenAIChatClient()

        # Create the conversational agent with instructions for pattern analysis
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="Pattern Analysis Agent",
            instructions="""You are an expert code pattern analyzer. Your role is to:

1. Analyze historical PR data to identify naming conventions
2. Extract common code patterns and structures
3. Identify file naming patterns (e.g., detector_*.py, test_*.py)
4. Extract common class names, function signatures, and import patterns
5. Provide confidence scores based on pattern frequency

When analyzing patterns:
- Look for consistency across multiple PRs
- Identify the most common conventions
- Note variations and edge cases
- Provide actionable recommendations

Format your findings as structured JSON with:
- pattern_type: "naming", "code_structure", "import", etc.
- pattern_value: the actual pattern (e.g., "detector_{rule_id}.py")
- confidence: 0.0 to 1.0 based on frequency
- occurrences: number of times seen
- examples: list of examples from PRs
            """,
        )

    async def analyze_pr_patterns(
        self,
        pr_data: List[Dict[str, Any]],
        focus_areas: Optional[List[str]] = None,
    ) -> List[CodePattern]:
        """
        Analyze PRs to extract patterns using LLM intelligence.

        Args:
            pr_data: List of PR dictionaries with files, titles, descriptions
            focus_areas: Optional list of areas to focus on (e.g., ["naming", "imports"])

        Returns:
            List of CodePattern objects with extracted patterns and confidence scores
        """
        if not pr_data:
            logger.warning("No PR data provided for pattern analysis")
            return self._get_default_patterns()

        # Prepare PR summary for LLM analysis
        pr_summary = self._summarize_prs_for_analysis(pr_data)

        # Build analysis prompt
        focus = ", ".join(focus_areas) if focus_areas else "all aspects"
        analysis_prompt = f"""Analyze these {len(pr_data)} detector-related PRs and extract patterns.

Focus areas: {focus}

PR Summary:
{pr_summary}

Please analyze and return a JSON array of patterns with this structure:
[
    {{
        "pattern_type": "file_naming",
        "pattern_value": "detector_{{rule_id}}.py",
        "confidence": 0.95,
        "occurrences": 18,
        "examples": ["detector_etw_rule_1.py", "detector_network_rule_2.py"]
    }},
    ...
]

Extract patterns for:
1. File naming conventions
2. Class naming patterns
3. Common function signatures
4. Import patterns
5. Code structure patterns
"""

        # Run LLM analysis
        logger.info("Running LLM pattern analysis", pr_count=len(pr_data))
        response = await self.agent.run(analysis_prompt)

        # Parse LLM response
        patterns = self._parse_pattern_response(response.text)

        logger.info("Pattern analysis complete", patterns_found=len(patterns))

        return patterns

    def _summarize_prs_for_analysis(self, pr_data: List[Dict[str, Any]]) -> str:
        """
        Create a concise summary of PRs for LLM analysis.

        Args:
            pr_data: List of PR dictionaries

        Returns:
            Formatted string summary of PRs
        """
        summary_parts = []

        for i, pr in enumerate(pr_data[:20], 1):  # Limit to 20 for token efficiency
            files_summary = [f["path"] for f in pr.get("files", [])[:10]]  # Limit files
            summary_parts.append(
                f"PR #{i} (ID: {pr.get('pr_id')})\n"
                f"  Title: {pr.get('title', 'N/A')}\n"
                f"  Files: {', '.join(files_summary)}\n"
            )

        return "\n".join(summary_parts)

    def _parse_pattern_response(self, response_text: str) -> List[CodePattern]:
        """
        Parse LLM response to extract pattern data.

        Args:
            response_text: Raw LLM response text

        Returns:
            List of CodePattern objects
        """
        patterns = []

        try:
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                pattern_data = json.loads(json_match.group())

                for item in pattern_data:
                    pattern = CodePattern(
                        pattern_type=item.get("pattern_type", "unknown"),
                        pattern_value=item.get("pattern_value", ""),
                        confidence=float(item.get("confidence", 0.0)),
                        occurrences=item.get("occurrences", 0),
                        examples=item.get("examples", []),
                    )
                    patterns.append(pattern)

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse LLM pattern response", error=str(e))
            # Fall back to basic pattern extraction
            patterns = self._extract_basic_patterns_from_text(response_text)

        # If no patterns found, use defaults
        if not patterns:
            patterns = self._get_default_patterns()

        return patterns

    def _extract_basic_patterns_from_text(self, text: str) -> List[CodePattern]:
        """
        Extract basic patterns from unstructured text response.

        Args:
            text: LLM response text

        Returns:
            List of CodePattern objects
        """
        patterns = []

        # Look for common detector patterns in text
        if "detector_" in text.lower():
            patterns.append(
                CodePattern(
                    pattern_type="file_naming",
                    pattern_value="detector_{rule_id}.py",
                    confidence=0.7,
                    occurrences=10,
                    examples=["detector_rule_1.py"],
                )
            )

        if "test_" in text.lower():
            patterns.append(
                CodePattern(
                    pattern_type="file_naming",
                    pattern_value="test_detector_{rule_id}.py",
                    confidence=0.7,
                    occurrences=10,
                    examples=["test_detector_rule_1.py"],
                )
            )

        return patterns

    def _get_default_patterns(self) -> List[CodePattern]:
        """
        Get default patterns when no PRs are available or analysis fails.

        Returns:
            List of default CodePattern objects
        """
        return [
            CodePattern(
                pattern_type="file_naming",
                pattern_value="detector_{rule_id}.py",
                confidence=0.5,
                occurrences=0,
                examples=["detector_example.py"],
                description="Default detector file naming pattern",
            ),
            CodePattern(
                pattern_type="file_naming",
                pattern_value="test_detector_{rule_id}.py",
                confidence=0.5,
                occurrences=0,
                examples=["test_detector_example.py"],
                description="Default test file naming pattern",
            ),
            CodePattern(
                pattern_type="class_naming",
                pattern_value="class {RuleName}Detector:",
                confidence=0.5,
                occurrences=0,
                examples=["class EtwDetector:"],
                description="Default detector class naming pattern",
            ),
            CodePattern(
                pattern_type="import",
                pattern_value="from shared.kusto_client import KustoClientWrapper",
                confidence=0.5,
                occurrences=0,
                examples=["from shared.kusto_client import KustoClientWrapper"],
                description="Default import pattern",
            ),
        ]


async def create_pattern_analysis_agent() -> PatternAnalysisAgent:
    """
    Factory function to create a Pattern Analysis Agent.

    Returns:
        Configured PatternAnalysisAgent instance using Azure OpenAI
    """
    return PatternAnalysisAgent()
