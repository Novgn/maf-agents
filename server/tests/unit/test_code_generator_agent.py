"""
Unit tests for Code Generator Agent.

Tests code generation from patterns and schema using mocked ChatAgent.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from agents.code_generator_agent import (
    CodeGeneratorAgent,
    create_code_generator_agent,
)
from shared.models import CodePattern, KustoSchemaField, GeneratedCodeData


class TestCodeGeneratorAgent:
    """Tests for CodeGeneratorAgent class."""

    @pytest.mark.asyncio
    async def test_agent_initialization_with_openai(self):
        """Test agent initialization with OpenAI client."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            assert agent.use_azure is False
            assert agent.agent is not None

    @pytest.mark.asyncio
    async def test_agent_initialization_with_azure(self):
        """Test agent initialization with Azure OpenAI client."""
        with patch("agents.code_generator_agent.AzureAzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            assert agent.use_azure is True
            assert agent.agent is not None

    @pytest.mark.asyncio
    async def test_generate_code_success(self):
        """Test successful code generation."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            # Mock ChatAgent response
            mock_agent = AsyncMock()
            mock_response = Mock()
            mock_response.text = """
DETECTOR_FILENAME: detector_test_rule.py
DETECTOR_CODE:
```python
\"\"\"Test detector.\"\"\"

class TestRuleDetector:
    def __init__(self):
        self.rule_id = "test_rule"

    async def detect(self):
        return False
```

TEST_FILENAME: test_detector_test_rule.py
TEST_CODE:
```python
import pytest

def test_detector():
    assert True
```
            """
            mock_agent.run = AsyncMock(return_value=mock_response)
            agent.agent = mock_agent

            # Sample data
            provider_guid = "12345678-1234-1234-1234-123456789012"
            rule_id = "test_rule"
            schema_fields = [
                KustoSchemaField(name="EventId", data_type="int", description="Event ID"),
                KustoSchemaField(name="Message", data_type="string", description="Message"),
            ]
            patterns = [
                CodePattern(
                    pattern_type="file_naming",
                    pattern_value="detector_{rule_id}.py",
                    confidence=0.95,
                    occurrences=10,
                    examples=["detector_rule1.py"],
                ),
            ]

            # Generate code
            result = await agent.generate_code(
                provider_guid, rule_id, schema_fields, patterns
            )

            # Verify result
            assert isinstance(result, GeneratedCodeData)
            assert result.detector_file_name == "detector_test_rule.py"
            assert "TestRuleDetector" in result.detector_code
            assert result.test_file_name == "test_detector_test_rule.py"
            assert result.test_code is not None
            assert "test_detector" in result.test_code

    @pytest.mark.asyncio
    async def test_validate_python_syntax_valid(self):
        """Test syntax validation with valid Python code."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            valid_code = """
def hello():
    return "world"
"""
            assert agent._validate_python_syntax(valid_code) is True

    @pytest.mark.asyncio
    async def test_validate_python_syntax_invalid(self):
        """Test syntax validation with invalid Python code."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            invalid_code = """
def hello(
    return "world"
"""
            assert agent._validate_python_syntax(invalid_code) is False

    @pytest.mark.asyncio
    async def test_validate_python_syntax_empty(self):
        """Test syntax validation with empty code."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            assert agent._validate_python_syntax("") is False
            assert agent._validate_python_syntax("   ") is False

    @pytest.mark.asyncio
    async def test_sanitize_class_name(self):
        """Test class name sanitization."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            assert agent._sanitize_class_name("test_rule") == "TestRule"
            assert agent._sanitize_class_name("test-rule-123") == "TestRule123"
            assert agent._sanitize_class_name("my.detector.rule") == "MyDetectorRule"

    @pytest.mark.asyncio
    async def test_format_schema_fields(self):
        """Test schema fields formatting for LLM prompt."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            fields = [
                KustoSchemaField(name="EventId", data_type="int", description="Event ID"),
                KustoSchemaField(name="Message", data_type="string"),
            ]

            formatted = agent._format_schema_fields(fields)

            assert "EventId" in formatted
            assert "int" in formatted
            assert "Message" in formatted

    @pytest.mark.asyncio
    async def test_format_schema_fields_empty(self):
        """Test schema fields formatting with empty list."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            formatted = agent._format_schema_fields([])

            assert "No schema fields available" in formatted

    @pytest.mark.asyncio
    async def test_format_patterns(self):
        """Test patterns formatting for LLM prompt."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            patterns = [
                CodePattern(
                    pattern_type="file_naming",
                    pattern_value="detector_{rule_id}.py",
                    confidence=0.95,
                    occurrences=10,
                ),
            ]

            formatted = agent._format_patterns(patterns)

            assert "file_naming" in formatted
            assert "detector_{rule_id}.py" in formatted
            assert "0.95" in formatted

    @pytest.mark.asyncio
    async def test_format_patterns_empty(self):
        """Test patterns formatting with empty list."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            formatted = agent._format_patterns([])

            assert "No specific patterns" in formatted

    @pytest.mark.asyncio
    async def test_parse_generated_code_complete(self):
        """Test parsing complete LLM response."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            response = """
DETECTOR_FILENAME: my_detector.py
DETECTOR_CODE:
```python
class MyDetector:
    pass
```

TEST_FILENAME: test_my_detector.py
TEST_CODE:
```python
def test_my_detector():
    pass
```
            """

            result = agent._parse_generated_code(response, "test_rule")

            assert result.detector_file_name == "my_detector.py"
            assert "MyDetector" in result.detector_code
            assert result.test_file_name == "test_my_detector.py"
            assert "test_my_detector" in result.test_code

    @pytest.mark.asyncio
    async def test_parse_generated_code_partial(self):
        """Test parsing partial LLM response with fallbacks."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            response = "Some text without proper format"

            result = agent._parse_generated_code(response, "test_rule")

            # Should use fallbacks
            assert "test_rule" in result.detector_file_name
            assert "TestRuleDetector" in result.detector_code
            assert result.test_code is None

    @pytest.mark.asyncio
    async def test_generate_fallback_detector_code(self):
        """Test fallback detector code generation."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            code = agent._generate_fallback_detector_code("my_test_rule")

            assert "MyTestRuleDetector" in code
            assert "my_test_rule" in code
            assert "def __init__" in code
            assert "async def detect" in code

    @pytest.mark.asyncio
    async def test_prepare_generation_context(self):
        """Test generation context preparation."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = CodeGeneratorAgent()

            provider_guid = "guid-123"
            rule_id = "rule-1"
            schema_fields = [
                KustoSchemaField(name="Field1", data_type="string", description="Desc1"),
            ]
            patterns = [
                CodePattern(
                    pattern_type="naming",
                    pattern_value="pattern_value",
                    confidence=0.9,
                    occurrences=5,
                ),
            ]

            context = agent._prepare_generation_context(
                provider_guid, rule_id, schema_fields, patterns
            )

            assert context["provider_guid"] == "guid-123"
            assert context["rule_id"] == "rule-1"
            assert len(context["schema_fields"]) == 1
            assert context["schema_fields"][0]["name"] == "Field1"
            assert len(context["patterns"]) == 1
            assert context["patterns"][0]["type"] == "naming"


class TestCreateCodeGeneratorAgent:
    """Tests for create_code_generator_agent factory function."""

    @pytest.mark.asyncio
    async def test_create_code_generator_agent_openai(self):
        """Test factory function creates agent with OpenAI client."""
        with patch("agents.code_generator_agent.AzureOpenAIChatClient"):
            agent = await create_code_generator_agent()

            assert isinstance(agent, CodeGeneratorAgent)
            assert agent.use_azure is False

    @pytest.mark.asyncio
    async def test_create_code_generator_agent_azure(self):
        """Test factory function creates agent with Azure client."""
        with patch("agents.code_generator_agent.AzureAzureOpenAIChatClient"):
            agent = await create_code_generator_agent()

            assert isinstance(agent, CodeGeneratorAgent)
            assert agent.use_azure is True
