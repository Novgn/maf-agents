"""
Unit tests for the ETW Input Collection Agent.

Tests validation logic and agent creation.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from agents.etw_input_agent import (
    validate_provider_guid,
    validate_rule_id,
    validate_etw_input,
    ETWInputAgent,
    create_etw_input_agent,
)
from shared.models import ETWInputData


class TestValidationFunctions:
    """Tests for validation functions."""

    def test_validate_provider_guid_valid(self):
        """Test validation with a valid GUID."""
        valid_guid = "12345678-1234-1234-1234-123456789012"
        is_valid, error = validate_provider_guid(valid_guid)
        assert is_valid is True
        assert error is None

    def test_validate_provider_guid_valid_lowercase(self):
        """Test validation with a valid lowercase GUID."""
        valid_guid = "abcdef12-3456-7890-abcd-ef1234567890"
        is_valid, error = validate_provider_guid(valid_guid)
        assert is_valid is True
        assert error is None

    def test_validate_provider_guid_valid_uppercase(self):
        """Test validation with a valid uppercase GUID."""
        valid_guid = "ABCDEF12-3456-7890-ABCD-EF1234567890"
        is_valid, error = validate_provider_guid(valid_guid)
        assert is_valid is True
        assert error is None

    def test_validate_provider_guid_valid_mixed_case(self):
        """Test validation with a valid mixed case GUID."""
        valid_guid = "AbCdEf12-3456-7890-aBcD-Ef1234567890"
        is_valid, error = validate_provider_guid(valid_guid)
        assert is_valid is True
        assert error is None

    def test_validate_provider_guid_empty(self):
        """Test validation with an empty GUID."""
        is_valid, error = validate_provider_guid("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_validate_provider_guid_invalid_format_no_hyphens(self):
        """Test validation with a GUID missing hyphens."""
        invalid_guid = "12345678123412341234123456789012"
        is_valid, error = validate_provider_guid(invalid_guid)
        assert is_valid is False
        assert "Invalid GUID format" in error

    def test_validate_provider_guid_invalid_format_wrong_length(self):
        """Test validation with a GUID of wrong length."""
        invalid_guid = "1234-1234-1234-1234"
        is_valid, error = validate_provider_guid(invalid_guid)
        assert is_valid is False
        assert "Invalid GUID format" in error

    def test_validate_provider_guid_invalid_format_non_hex(self):
        """Test validation with a GUID containing non-hexadecimal characters."""
        invalid_guid = "GGGGGGGG-1234-1234-1234-123456789012"
        is_valid, error = validate_provider_guid(invalid_guid)
        assert is_valid is False
        assert "Invalid GUID format" in error

    def test_validate_provider_guid_invalid_format_wrong_section_lengths(self):
        """Test validation with a GUID having wrong section lengths."""
        invalid_guid = "123-12345-1234-1234-123456789012"
        is_valid, error = validate_provider_guid(invalid_guid)
        assert is_valid is False
        assert "Invalid GUID format" in error

    def test_validate_rule_id_valid(self):
        """Test validation with a valid rule ID."""
        valid_rule_id = "test-detector-rule-1"
        is_valid, error = validate_rule_id(valid_rule_id)
        assert is_valid is True
        assert error is None

    def test_validate_rule_id_valid_with_numbers(self):
        """Test validation with a rule ID containing numbers."""
        valid_rule_id = "detector-123"
        is_valid, error = validate_rule_id(valid_rule_id)
        assert is_valid is True
        assert error is None

    def test_validate_rule_id_valid_with_underscores(self):
        """Test validation with a rule ID containing underscores."""
        valid_rule_id = "detector_rule_1"
        is_valid, error = validate_rule_id(valid_rule_id)
        assert is_valid is True
        assert error is None

    def test_validate_rule_id_empty(self):
        """Test validation with an empty rule ID."""
        is_valid, error = validate_rule_id("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_validate_rule_id_whitespace_only(self):
        """Test validation with a rule ID containing only whitespace."""
        is_valid, error = validate_rule_id("   ")
        assert is_valid is False
        assert "cannot be empty" in error


class TestValidateETWInputTool:
    """Tests for the validate_etw_input tool function."""

    @pytest.mark.asyncio
    async def test_validate_etw_input_success(self):
        """Test successful validation of both inputs."""
        result = await validate_etw_input(
            provider_guid="12345678-1234-1234-1234-123456789012",
            rule_id="test-detector-rule-1"
        )
        assert "✅ Validation Successful" in result
        assert "12345678-1234-1234-1234-123456789012" in result
        assert "test-detector-rule-1" in result

    @pytest.mark.asyncio
    async def test_validate_etw_input_invalid_guid(self):
        """Test validation with invalid provider GUID."""
        result = await validate_etw_input(
            provider_guid="invalid-guid",
            rule_id="test-detector-rule-1"
        )
        assert "❌ Validation Failed" in result
        assert "Invalid GUID format" in result

    @pytest.mark.asyncio
    async def test_validate_etw_input_empty_guid(self):
        """Test validation with empty provider GUID."""
        result = await validate_etw_input(
            provider_guid="",
            rule_id="test-detector-rule-1"
        )
        assert "❌ Validation Failed" in result
        assert "cannot be empty" in result

    @pytest.mark.asyncio
    async def test_validate_etw_input_empty_rule_id(self):
        """Test validation with empty rule ID."""
        result = await validate_etw_input(
            provider_guid="12345678-1234-1234-1234-123456789012",
            rule_id=""
        )
        assert "❌ Validation Failed" in result
        assert "cannot be empty" in result


class TestETWInputAgent:
    """Tests for the ETWInputAgent class."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization with Azure OpenAI client."""
        with patch("agents.etw_input_agent.AzureOpenAIChatClient") as mock_client:
            agent = ETWInputAgent()
            mock_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_inputs_pre_populated_valid(self):
        """Test collect_inputs with pre-populated valid data."""
        with patch("agents.etw_input_agent.AzureOpenAIChatClient"):
            agent = ETWInputAgent()

            result = await agent.collect_inputs(
                provider_guid="12345678-1234-1234-1234-123456789012",
                rule_id="test-detector-rule-1"
            )

            assert isinstance(result, ETWInputData)
            assert result.provider_guid == "12345678-1234-1234-1234-123456789012"
            assert result.rule_id == "test-detector-rule-1"

    @pytest.mark.asyncio
    async def test_collect_inputs_pre_populated_invalid_guid(self):
        """Test collect_inputs with pre-populated invalid GUID."""
        with patch("agents.etw_input_agent.AzureOpenAIChatClient"):
            agent = ETWInputAgent()

            with pytest.raises(ValueError, match="Invalid GUID format"):
                await agent.collect_inputs(
                    provider_guid="invalid-guid",
                    rule_id="test-detector-rule-1"
                )

    @pytest.mark.asyncio
    async def test_collect_inputs_pre_populated_empty_rule_id(self):
        """Test collect_inputs with pre-populated empty rule ID."""
        with patch("agents.etw_input_agent.AzureOpenAIChatClient"):
            agent = ETWInputAgent()

            with pytest.raises(ValueError, match="Rule ID cannot be empty"):
                await agent.collect_inputs(
                    provider_guid="12345678-1234-1234-1234-123456789012",
                    rule_id=""
                )

    @pytest.mark.asyncio
    async def test_collect_inputs_conversational_success(self):
        """Test collect_inputs with conversational flow (mocked)."""
        with patch("agents.etw_input_agent.AzureOpenAIChatClient"), \
             patch("agents.etw_input_agent.input") as mock_input:

            # Mock ChatAgent
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value="Mock agent response")

            agent = ETWInputAgent()
            agent.agent = mock_agent

            # Simulate user inputs
            mock_input.side_effect = [
                "12345678-1234-1234-1234-123456789012",  # Provider GUID
                "test-detector-rule-1"                   # Rule ID
            ]

            result = await agent.collect_inputs()

            assert isinstance(result, ETWInputData)
            assert result.provider_guid == "12345678-1234-1234-1234-123456789012"
            assert result.rule_id == "test-detector-rule-1"

    @pytest.mark.asyncio
    async def test_collect_inputs_conversational_invalid_guid_retry(self):
        """Test collect_inputs with invalid GUID and retry."""
        with patch("agents.etw_input_agent.AzureOpenAIChatClient"), \
             patch("agents.etw_input_agent.input") as mock_input:

            # Mock ChatAgent
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value="Mock agent response")

            agent = ETWInputAgent()
            agent.agent = mock_agent

            # Simulate user inputs: invalid GUID first, then valid
            mock_input.side_effect = [
                "invalid-guid",                          # Invalid GUID
                "12345678-1234-1234-1234-123456789012",  # Valid GUID
                "test-detector-rule-1"                   # Rule ID
            ]

            result = await agent.collect_inputs()

            assert isinstance(result, ETWInputData)
            assert result.provider_guid == "12345678-1234-1234-1234-123456789012"
            assert result.rule_id == "test-detector-rule-1"


class TestCreateETWInputAgent:
    """Tests for the create_etw_input_agent factory function."""

    @pytest.mark.asyncio
    async def test_create_etw_input_agent(self):
        """Test factory function creates agent with Azure OpenAI client."""
        with patch("agents.etw_input_agent.AzureOpenAIChatClient"):
            agent = await create_etw_input_agent()
            assert isinstance(agent, ETWInputAgent)
