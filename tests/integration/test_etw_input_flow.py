"""
Integration tests for ETW Input Collection Agent workflow.

Tests the conversational flow and integration with the workflow orchestrator.
"""

import pytest
from unittest.mock import patch, AsyncMock

from agents.etw_input_agent import create_etw_input_agent, ETWInputAgent
from shared.models import ETWInputData


class TestETWInputConversationalFlow:
    """Integration tests for the conversational flow of ETW Input Agent."""

    @pytest.mark.asyncio
    async def test_full_conversational_flow_with_valid_inputs(self):
        """
        Test complete conversational flow with valid inputs provided by user.

        This simulates a user providing valid providerGuid and ruleId
        through the conversational interface.
        """
        with patch("agents.etw_input_agent.OpenAIChatClient"), \
             patch("agents.etw_input_agent.input") as mock_input:

            # Mock the ChatAgent
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value="Mock conversational response")

            # Create the ETW Input Agent
            agent = await create_etw_input_agent(use_azure=False)
            agent.agent = mock_agent

            # Simulate user providing valid inputs
            mock_input.side_effect = [
                "12345678-1234-1234-1234-123456789012",  # Valid provider GUID
                "test-detector-rule-1"                   # Valid rule ID
            ]

            # Run the conversational collection
            result = await agent.collect_inputs()

            # Verify the result
            assert isinstance(result, ETWInputData)
            assert result.provider_guid == "12345678-1234-1234-1234-123456789012"
            assert result.rule_id == "test-detector-rule-1"

            # Verify agent interactions
            assert mock_agent.run.call_count >= 2  # Initial prompt + confirmation

    @pytest.mark.asyncio
    async def test_conversational_flow_with_invalid_guid_then_valid(self):
        """
        Test conversational flow with invalid GUID followed by valid input.

        This simulates a user making an error and then providing correct input
        after receiving helpful error messages.
        """
        with patch("agents.etw_input_agent.OpenAIChatClient"), \
             patch("agents.etw_input_agent.input") as mock_input:

            # Mock the ChatAgent
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value="Mock error and retry response")

            # Create the ETW Input Agent
            agent = await create_etw_input_agent(use_azure=False)
            agent.agent = mock_agent

            # Simulate user providing invalid GUID first, then valid inputs
            mock_input.side_effect = [
                "not-a-valid-guid",                      # Invalid GUID
                "ABCDEF12-3456-7890-ABCD-EF1234567890",  # Valid GUID (uppercase)
                "detector-rule-123"                      # Valid rule ID
            ]

            # Run the conversational collection
            result = await agent.collect_inputs()

            # Verify the result
            assert isinstance(result, ETWInputData)
            assert result.provider_guid == "ABCDEF12-3456-7890-ABCD-EF1234567890"
            assert result.rule_id == "detector-rule-123"

            # Verify agent provided error feedback
            assert mock_agent.run.call_count >= 3  # Initial + error + confirmation

    @pytest.mark.asyncio
    async def test_conversational_flow_with_invalid_rule_id_then_valid(self):
        """
        Test conversational flow with empty rule ID followed by valid input.

        This simulates a user skipping the rule ID and then providing it
        after receiving an error message.
        """
        with patch("agents.etw_input_agent.OpenAIChatClient"), \
             patch("agents.etw_input_agent.input") as mock_input:

            # Mock the ChatAgent
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value="Mock error and retry response")

            # Create the ETW Input Agent
            agent = await create_etw_input_agent(use_azure=False)
            agent.agent = mock_agent

            # Simulate user providing valid GUID but empty rule ID first
            mock_input.side_effect = [
                "12345678-1234-1234-1234-123456789012",  # Valid GUID
                "",                                       # Empty rule ID (invalid)
                "valid-rule-id"                          # Valid rule ID
            ]

            # Run the conversational collection
            result = await agent.collect_inputs()

            # Verify the result
            assert isinstance(result, ETWInputData)
            assert result.provider_guid == "12345678-1234-1234-1234-123456789012"
            assert result.rule_id == "valid-rule-id"

    @pytest.mark.asyncio
    async def test_conversational_flow_max_attempts_exceeded(self):
        """
        Test conversational flow when max attempts are exceeded.

        This simulates a user repeatedly providing invalid inputs and
        verifies that the agent fails gracefully after max attempts.
        """
        with patch("agents.etw_input_agent.OpenAIChatClient"), \
             patch("agents.etw_input_agent.input") as mock_input:

            # Mock the ChatAgent
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value="Mock error response")

            # Create the ETW Input Agent
            agent = await create_etw_input_agent(use_azure=False)
            agent.agent = mock_agent

            # Simulate user providing invalid inputs repeatedly
            mock_input.side_effect = [
                "invalid-guid-1",  # Attempt 1
                "invalid-guid-2",  # Attempt 2
                "invalid-guid-3",  # Attempt 3
            ]

            # Verify that the agent raises ValueError after max attempts
            with pytest.raises(ValueError, match="Failed to collect valid inputs"):
                await agent.collect_inputs()

    @pytest.mark.asyncio
    async def test_pre_populated_inputs_bypass_conversation(self):
        """
        Test that pre-populated inputs bypass the conversational flow.

        This simulates automated workflows where inputs are provided
        programmatically without user interaction.
        """
        with patch("agents.etw_input_agent.OpenAIChatClient"):
            # Create the ETW Input Agent
            agent = await create_etw_input_agent(use_azure=False)

            # Provide pre-populated inputs
            result = await agent.collect_inputs(
                provider_guid="87654321-4321-4321-4321-210987654321",
                rule_id="automated-detector-rule"
            )

            # Verify the result
            assert isinstance(result, ETWInputData)
            assert result.provider_guid == "87654321-4321-4321-4321-210987654321"
            assert result.rule_id == "automated-detector-rule"

    @pytest.mark.asyncio
    async def test_workflow_integration_with_etw_agent(self):
        """
        Test integration of ETW Input Agent with the workflow orchestrator.

        This tests that the agent can be properly integrated into the
        workflow and returns data in the expected format.
        """
        with patch("agents.etw_input_agent.OpenAIChatClient"):
            # Create the ETW Input Agent
            agent = await create_etw_input_agent(use_azure=False)

            # Simulate workflow providing pre-populated data
            result = await agent.collect_inputs(
                provider_guid="11111111-2222-3333-4444-555555555555",
                rule_id="workflow-detector-rule"
            )

            # Verify the result is in the correct format for workflow state
            assert isinstance(result, ETWInputData)
            assert hasattr(result, "provider_guid")
            assert hasattr(result, "rule_id")
            assert result.provider_guid == "11111111-2222-3333-4444-555555555555"
            assert result.rule_id == "workflow-detector-rule"

            # Verify the model can be serialized (for checkpoint persistence)
            data_dict = result.model_dump()
            assert "provider_guid" in data_dict
            assert "rule_id" in data_dict

    @pytest.mark.asyncio
    async def test_conversational_flow_with_mixed_case_guid(self):
        """
        Test that the agent accepts GUIDs in mixed case.

        This verifies that the validation is case-insensitive.
        """
        with patch("agents.etw_input_agent.OpenAIChatClient"), \
             patch("agents.etw_input_agent.input") as mock_input:

            # Mock the ChatAgent
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value="Mock response")

            # Create the ETW Input Agent
            agent = await create_etw_input_agent(use_azure=False)
            agent.agent = mock_agent

            # Simulate user providing mixed case GUID
            mock_input.side_effect = [
                "AbCdEf12-3456-7890-aBcD-Ef1234567890",  # Mixed case GUID
                "test-rule"                              # Rule ID
            ]

            # Run the conversational collection
            result = await agent.collect_inputs()

            # Verify the result
            assert isinstance(result, ETWInputData)
            assert result.provider_guid == "AbCdEf12-3456-7890-aBcD-Ef1234567890"
            assert result.rule_id == "test-rule"
