"""
Code Generator Agent using Microsoft Agent Framework.

This module implements an agent that generates detector code files using
LLM intelligence (ChatAgent) based on learned patterns and ETW schema.
"""

from typing import Optional, List, Dict, Any
import ast
import re

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient

from shared.models import CodePattern, KustoSchemaField, GeneratedCodeData
import structlog

logger = structlog.get_logger(__name__)


class CodeGeneratorAgent:
    """
    Code Generator Agent using Microsoft Agent Framework.

    This agent uses LLM intelligence (ChatAgent) to generate detector code files
    following learned patterns and conventions from historical PRs.
    """

    def __init__(self):
        """
        Initialize the Code Generator Agent.

        Uses Azure OpenAI for LLM-based code generation.
        """
        # Create the chat client
        chat_client = AzureOpenAIChatClient()

        # Create the conversational agent for code generation
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="Code Generator Agent",
            instructions="""You are an expert Python developer specializing in generating detector code for Azure monitoring systems.

Your responsibilities:
1. Generate detector Python code following established patterns and conventions
2. Incorporate ETW schema fields into detector logic
3. Follow naming conventions from historical PRs
4. Include proper imports, class definitions, and event handling
5. Generate corresponding test files with basic unit test skeletons
6. Ensure generated code is syntactically valid Python
7. Present code preview conversationally before finalizing

Code Generation Guidelines:
- Use provided patterns for file names, class names, and structure
- Incorporate all relevant ETW schema fields
- Include docstrings and type hints
- Follow PEP 8 style guidelines
- Generate clean, maintainable code
- Include error handling where appropriate

Test Generation Guidelines:
- Generate pytest-compatible test files
- Include basic test class and test methods
- Mock external dependencies (Kusto, etc.)
- Follow test patterns from historical PRs
            """,
        )

    async def generate_code(
        self,
        provider_guid: str,
        rule_id: str,
        schema_fields: List[KustoSchemaField],
        patterns: List[CodePattern],
    ) -> GeneratedCodeData:
        """
        Generate detector code using LLM intelligence.

        Args:
            provider_guid: ETW provider GUID
            rule_id: Rule ID for the detector
            schema_fields: List of schema fields from Kusto
            patterns: List of code patterns extracted from historical PRs

        Returns:
            GeneratedCodeData with detector and test code
        """
        logger.info(
            "Starting code generation",
            rule_id=rule_id,
            schema_field_count=len(schema_fields),
            pattern_count=len(patterns),
        )

        # Prepare context for code generation
        context = self._prepare_generation_context(
            provider_guid, rule_id, schema_fields, patterns
        )

        # Build generation prompt
        generation_prompt = f"""Generate a complete Python detector implementation with the following requirements:

**ETW Details:**
- Provider GUID: {provider_guid}
- Rule ID: {rule_id}

**Schema Fields:**
{self._format_schema_fields(schema_fields)}

**Patterns to Follow:**
{self._format_patterns(patterns)}

**Requirements:**
1. Generate a detector Python file following the naming pattern
2. Include all necessary imports
3. Create a detector class with proper initialization
4. Implement ETW event handling logic using schema fields
5. Add docstrings and type hints
6. Ensure code is syntactically valid

Please generate the complete detector code. Format your response as:

DETECTOR_FILENAME: filename.py
DETECTOR_CODE:
```python
# Your detector code here
```

TEST_FILENAME: test_filename.py
TEST_CODE:
```python
# Your test code here
```
"""

        # Run LLM code generation
        logger.info("Running LLM code generation")
        response = await self.agent.run(generation_prompt)

        # Parse generated code from response
        generated_data = self._parse_generated_code(response.text, rule_id)

        # Validate syntax
        detector_valid = self._validate_python_syntax(generated_data.detector_code)
        test_valid = self._validate_python_syntax(generated_data.test_code or "")

        if not detector_valid:
            logger.warning("Generated detector code has syntax errors")
        if generated_data.test_code and not test_valid:
            logger.warning("Generated test code has syntax errors")

        logger.info(
            "Code generation complete",
            detector_file=generated_data.detector_file_name,
            test_file=generated_data.test_file_name,
            detector_valid=detector_valid,
            test_valid=test_valid,
        )

        return generated_data

    def _prepare_generation_context(
        self,
        provider_guid: str,
        rule_id: str,
        schema_fields: List[KustoSchemaField],
        patterns: List[CodePattern],
    ) -> Dict[str, Any]:
        """
        Prepare context dictionary for code generation.

        Args:
            provider_guid: ETW provider GUID
            rule_id: Rule ID
            schema_fields: Schema fields
            patterns: Code patterns

        Returns:
            Context dictionary
        """
        return {
            "provider_guid": provider_guid,
            "rule_id": rule_id,
            "schema_fields": [
                {"name": f.name, "type": f.data_type, "description": f.description}
                for f in schema_fields
            ],
            "patterns": [
                {
                    "type": p.pattern_type,
                    "value": p.pattern_value,
                    "confidence": p.confidence,
                }
                for p in patterns
            ],
        }

    def _format_schema_fields(self, schema_fields: List[KustoSchemaField]) -> str:
        """
        Format schema fields for LLM prompt.

        Args:
            schema_fields: List of schema fields

        Returns:
            Formatted string
        """
        if not schema_fields:
            return "No schema fields available"

        lines = []
        for field in schema_fields[:20]:  # Limit for token efficiency
            desc = field.description or "No description"
            lines.append(f"- {field.name} ({field.data_type}): {desc}")

        if len(schema_fields) > 20:
            lines.append(f"... and {len(schema_fields) - 20} more fields")

        return "\n".join(lines)

    def _format_patterns(self, patterns: List[CodePattern]) -> str:
        """
        Format code patterns for LLM prompt.

        Args:
            patterns: List of code patterns

        Returns:
            Formatted string
        """
        if not patterns:
            return "No specific patterns available - use standard conventions"

        lines = []
        for pattern in patterns[:10]:  # Limit for token efficiency
            lines.append(
                f"- {pattern.pattern_type}: {pattern.pattern_value} (confidence: {pattern.confidence:.2f})"
            )

        return "\n".join(lines)

    def _parse_generated_code(self, response_text: str, rule_id: str) -> GeneratedCodeData:
        """
        Parse generated code from LLM response.

        Args:
            response_text: LLM response text
            rule_id: Rule ID for fallback naming

        Returns:
            GeneratedCodeData object
        """
        # Extract detector filename
        detector_filename_match = re.search(
            r"DETECTOR_FILENAME:\s*(\S+)", response_text
        )
        detector_filename = (
            detector_filename_match.group(1)
            if detector_filename_match
            else f"detector_{rule_id}.py"
        )

        # Extract detector code
        detector_code_match = re.search(
            r"DETECTOR_CODE:\s*```python\n(.*?)```", response_text, re.DOTALL
        )
        detector_code = (
            detector_code_match.group(1).strip()
            if detector_code_match
            else self._generate_fallback_detector_code(rule_id)
        )

        # Extract test filename
        test_filename_match = re.search(r"TEST_FILENAME:\s*(\S+)", response_text)
        test_filename = (
            test_filename_match.group(1)
            if test_filename_match
            else f"test_detector_{rule_id}.py"
        )

        # Extract test code
        test_code_match = re.search(
            r"TEST_CODE:\s*```python\n(.*?)```", response_text, re.DOTALL
        )
        test_code = test_code_match.group(1).strip() if test_code_match else None

        return GeneratedCodeData(
            detector_file_name=detector_filename,
            detector_code=detector_code,
            test_file_name=test_filename,
            test_code=test_code,
        )

    def _generate_fallback_detector_code(self, rule_id: str) -> str:
        """
        Generate fallback detector code if LLM response parsing fails.

        Args:
            rule_id: Rule ID

        Returns:
            Basic detector code template
        """
        return f'''"""
Detector for rule {rule_id}.

This detector monitors ETW events and triggers alerts based on defined conditions.
"""

from shared.kusto_client import KustoClientWrapper


class {self._sanitize_class_name(rule_id)}Detector:
    """Detector implementation for {rule_id}."""

    def __init__(self, kusto_client: KustoClientWrapper):
        """
        Initialize the detector.

        Args:
            kusto_client: Kusto client for querying ETW data
        """
        self.kusto_client = kusto_client
        self.rule_id = "{rule_id}"

    async def detect(self) -> bool:
        """
        Run detection logic.

        Returns:
            True if condition detected, False otherwise
        """
        # TODO: Implement detection logic
        return False
'''

    def _sanitize_class_name(self, rule_id: str) -> str:
        """
        Sanitize rule ID for use as Python class name.

        Args:
            rule_id: Rule ID

        Returns:
            Sanitized class name
        """
        # Remove non-alphanumeric characters and convert to PascalCase
        sanitized = re.sub(r'[^a-zA-Z0-9]', '_', rule_id)
        parts = sanitized.split('_')
        return ''.join(word.capitalize() for word in parts if word)

    def _validate_python_syntax(self, code: str) -> bool:
        """
        Validate Python code syntax using AST parsing.

        Args:
            code: Python code string

        Returns:
            True if syntax is valid, False otherwise
        """
        if not code or not code.strip():
            return False

        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            logger.warning("Syntax validation failed", error=str(e))
            return False


async def create_code_generator_agent() -> CodeGeneratorAgent:
    """
    Factory function to create a Code Generator Agent.

    Returns:
        Configured CodeGeneratorAgent instance using Azure OpenAI
    """
    return CodeGeneratorAgent()
