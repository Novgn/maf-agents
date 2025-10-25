"""
Unit tests for Pattern Analysis Agent.

Tests pattern extraction from PR data using mocked ChatAgent.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from agents.pattern_analysis_agent import (
    PatternAnalysisAgent,
    create_pattern_analysis_agent,
)
from shared.models import CodePattern


class TestPatternAnalysisAgent:
    """Tests for PatternAnalysisAgent class."""

    @pytest.mark.asyncio
    async def test_agent_initialization_with_openai(self):
        """Test agent initialization with OpenAI client."""
        with patch("agents.pattern_analysis_agent.OpenAIChatClient"):
            agent = PatternAnalysisAgent(use_azure=False)

            assert agent.use_azure is False
            assert agent.agent is not None

    @pytest.mark.asyncio
    async def test_agent_initialization_with_azure(self):
        """Test agent initialization with Azure OpenAI client."""
        with patch("agents.pattern_analysis_agent.AzureOpenAIChatClient"):
            agent = PatternAnalysisAgent(use_azure=True)

            assert agent.use_azure is True
            assert agent.agent is not None

    @pytest.mark.asyncio
    async def test_analyze_pr_patterns_with_data(self):
        """Test pattern analysis with PR data."""
        with patch("agents.pattern_analysis_agent.OpenAIChatClient"):
            agent = PatternAnalysisAgent(use_azure=False)

            # Mock the ChatAgent
            mock_agent = AsyncMock()
            mock_response = Mock()
            mock_response.text = """
[
    {
        "pattern_type": "file_naming",
        "pattern_value": "detector_{rule_id}.py",
        "confidence": 0.95,
        "occurrences": 18,
        "examples": ["detector_etw_rule_1.py", "detector_network_rule_2.py"]
    },
    {
        "pattern_type": "class_naming",
        "pattern_value": "class {RuleName}Detector:",
        "confidence": 0.90,
        "occurrences": 15,
        "examples": ["class EtwDetector:", "class NetworkDetector:"]
    }
]
            """
            mock_agent.run = AsyncMock(return_value=mock_response)
            agent.agent = mock_agent

            # Sample PR data
            pr_data = [
                {
                    "pr_id": 1,
                    "title": "Add ETW detector for rule 1",
                    "files": [
                        {"path": "detector_etw_rule_1.py"},
                        {"path": "test_detector_etw_rule_1.py"},
                    ],
                },
                {
                    "pr_id": 2,
                    "title": "Add network detector for rule 2",
                    "files": [
                        {"path": "detector_network_rule_2.py"},
                        {"path": "test_detector_network_rule_2.py"},
                    ],
                },
            ]

            # Run analysis
            patterns = await agent.analyze_pr_patterns(pr_data)

            # Verify results
            assert len(patterns) == 2
            assert isinstance(patterns[0], CodePattern)
            assert patterns[0].pattern_type == "file_naming"
            assert patterns[0].confidence == 0.95
            assert patterns[0].occurrences == 18
            assert patterns[1].pattern_type == "class_naming"

    @pytest.mark.asyncio
    async def test_analyze_pr_patterns_empty_data(self):
        """Test pattern analysis with empty PR data."""
        with patch("agents.pattern_analysis_agent.OpenAIChatClient"):
            agent = PatternAnalysisAgent(use_azure=False)

            # Run analysis with empty data
            patterns = await agent.analyze_pr_patterns([])

            # Should return default patterns
            assert len(patterns) > 0
            assert all(isinstance(p, CodePattern) for p in patterns)
            assert any(p.pattern_type == "file_naming" for p in patterns)

    @pytest.mark.asyncio
    async def test_analyze_pr_patterns_with_focus_areas(self):
        """Test pattern analysis with specific focus areas."""
        with patch("agents.pattern_analysis_agent.OpenAIChatClient"):
            agent = PatternAnalysisAgent(use_azure=False)

            # Mock the ChatAgent
            mock_agent = AsyncMock()
            mock_response = Mock()
            mock_response.text = """
[
    {
        "pattern_type": "import",
        "pattern_value": "from shared.kusto_client import KustoClientWrapper",
        "confidence": 0.88,
        "occurrences": 20,
        "examples": ["from shared.kusto_client import KustoClientWrapper"]
    }
]
            """
            mock_agent.run = AsyncMock(return_value=mock_response)
            agent.agent = mock_agent

            pr_data = [{"pr_id": 1, "title": "Test PR", "files": []}]

            # Run analysis with focus areas
            patterns = await agent.analyze_pr_patterns(
                pr_data, focus_areas=["imports", "naming"]
            )

            # Verify focus areas were used
            assert mock_agent.run.called
            call_args = mock_agent.run.call_args[0][0]
            assert "imports, naming" in call_args

            # Verify results
            assert len(patterns) > 0
            assert patterns[0].pattern_type == "import"

    @pytest.mark.asyncio
    async def test_parse_pattern_response_valid_json(self):
        """Test parsing valid JSON response."""
        with patch("agents.pattern_analysis_agent.OpenAIChatClient"):
            agent = PatternAnalysisAgent(use_azure=False)

            response_text = """
Here are the patterns I found:
[
    {
        "pattern_type": "file_naming",
        "pattern_value": "detector_*.py",
        "confidence": 0.95,
        "occurrences": 10,
        "examples": ["detector_test.py"]
    }
]
            """

            patterns = agent._parse_pattern_response(response_text)

            assert len(patterns) == 1
            assert patterns[0].pattern_type == "file_naming"
            assert patterns[0].confidence == 0.95

    @pytest.mark.asyncio
    async def test_parse_pattern_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        with patch("agents.pattern_analysis_agent.OpenAIChatClient"):
            agent = PatternAnalysisAgent(use_azure=False)

            response_text = "This is not JSON, but mentions detector_ patterns"

            patterns = agent._parse_pattern_response(response_text)

            # Should fall back to basic extraction
            assert len(patterns) > 0
            assert any("detector_" in p.pattern_value for p in patterns)

    @pytest.mark.asyncio
    async def test_summarize_prs_for_analysis(self):
        """Test PR summarization for LLM analysis."""
        with patch("agents.pattern_analysis_agent.OpenAIChatClient"):
            agent = PatternAnalysisAgent(use_azure=False)

            pr_data = [
                {
                    "pr_id": 123,
                    "title": "Add detector",
                    "files": [{"path": "detector_test.py"}, {"path": "test_detector.py"}],
                },
                {
                    "pr_id": 456,
                    "title": "Fix detector",
                    "files": [{"path": "detector_fix.py"}],
                },
            ]

            summary = agent._summarize_prs_for_analysis(pr_data)

            # Verify summary contains key information
            assert "PR #1" in summary
            assert "123" in summary
            assert "Add detector" in summary
            assert "detector_test.py" in summary

    @pytest.mark.asyncio
    async def test_get_default_patterns(self):
        """Test default pattern generation."""
        with patch("agents.pattern_analysis_agent.OpenAIChatClient"):
            agent = PatternAnalysisAgent(use_azure=False)

            patterns = agent._get_default_patterns()

            # Verify default patterns
            assert len(patterns) >= 4
            pattern_types = {p.pattern_type for p in patterns}
            assert "file_naming" in pattern_types
            assert "class_naming" in pattern_types
            assert "import" in pattern_types

            # All should have confidence 0.5 (default)
            assert all(p.confidence == 0.5 for p in patterns)

    @pytest.mark.asyncio
    async def test_extract_basic_patterns_from_text(self):
        """Test basic pattern extraction from unstructured text."""
        with patch("agents.pattern_analysis_agent.OpenAIChatClient"):
            agent = PatternAnalysisAgent(use_azure=False)

            text = """
I found several patterns:
- Files follow detector_{name}.py pattern
- Tests use test_detector_{name}.py pattern
            """

            patterns = agent._extract_basic_patterns_from_text(text)

            # Should extract basic patterns
            assert len(patterns) >= 2
            pattern_values = {p.pattern_value for p in patterns}
            assert any("detector_" in v for v in pattern_values)
            assert any("test_" in v for v in pattern_values)


class TestCreatePatternAnalysisAgent:
    """Tests for create_pattern_analysis_agent factory function."""

    @pytest.mark.asyncio
    async def test_create_pattern_analysis_agent_openai(self):
        """Test factory function creates agent with OpenAI client."""
        with patch("agents.pattern_analysis_agent.OpenAIChatClient"):
            agent = await create_pattern_analysis_agent(use_azure=False)

            assert isinstance(agent, PatternAnalysisAgent)
            assert agent.use_azure is False

    @pytest.mark.asyncio
    async def test_create_pattern_analysis_agent_azure(self):
        """Test factory function creates agent with Azure client."""
        with patch("agents.pattern_analysis_agent.AzureOpenAIChatClient"):
            agent = await create_pattern_analysis_agent(use_azure=True)

            assert isinstance(agent, PatternAnalysisAgent)
            assert agent.use_azure is True
