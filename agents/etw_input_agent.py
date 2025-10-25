"""
ETW Input Collection Agent using Microsoft Agent Framework.

This module implements a conversational agent that collects and validates
ETW providerGuid and ruleId from users in a natural, guided manner.
"""

import re
from typing import Annotated, Optional
from pydantic import Field

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient

from shared.models import ETWInputData


# Validation functions
def validate_provider_guid(guid: str) -> tuple[bool, Optional[str]]:
    """
    Validate that the provider GUID is in the correct UUID format.

    Args:
        guid: The GUID string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    guid_pattern = re.compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )

    if not guid:
        return False, "Provider GUID cannot be empty."

    if not guid_pattern.match(guid):
        return False, (
            f"Invalid GUID format: '{guid}'. "
            "Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx "
            "(e.g., 12345678-1234-1234-1234-123456789012)"
        )

    return True, None


def validate_rule_id(rule_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate that the rule ID is not empty.

    Args:
        rule_id: The rule ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not rule_id or not rule_id.strip():
        return False, "Rule ID cannot be empty."

    return True, None


# Tool functions for the agent
async def validate_etw_input(
    provider_guid: Annotated[str, Field(description="The ETW provider GUID in UUID format")],
    rule_id: Annotated[str, Field(description="The rule ID for the detector")]
) -> str:
    """
    Validate ETW input parameters (providerGuid and ruleId).

    This tool validates that the provider GUID is in correct UUID format
    and that the rule ID is not empty.

    Args:
        provider_guid: The ETW provider GUID
        rule_id: The detector rule ID

    Returns:
        Validation result message
    """
    # Validate provider GUID
    guid_valid, guid_error = validate_provider_guid(provider_guid)
    if not guid_valid:
        return f"❌ Validation Failed: {guid_error}"

    # Validate rule ID
    rule_valid, rule_error = validate_rule_id(rule_id)
    if not rule_valid:
        return f"❌ Validation Failed: {rule_error}"

    # Both valid
    return f"✅ Validation Successful! Provider GUID: {provider_guid}, Rule ID: {rule_id}"


class ETWInputAgent:
    """
    ETW Input Collection Agent using Microsoft Agent Framework.

    This agent provides a conversational interface for collecting and validating
    ETW provider GUID and rule ID from detector engineers.
    """

    def __init__(self):
        """
        Initialize the ETW Input Agent.

        Uses Azure OpenAI for conversational input collection.
        """
        # Create the chat client
        chat_client = AzureOpenAIChatClient()

        # Create the conversational agent
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="ETW Input Collector",
            instructions="""You are a helpful assistant that collects ETW (Event Tracing for Windows)
information from detector engineers. Your role is to guide users through providing:

1. **Provider GUID**: An ETW provider GUID in UUID format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
2. **Rule ID**: A unique identifier for the detector rule

Be conversational, friendly, and helpful. When collecting information:
- Ask for one piece of information at a time
- Explain what each field is used for
- If validation fails, provide clear error messages and ask again
- Confirm the information before finalizing

Start by greeting the user and asking for the ETW provider GUID first, then the rule ID.
Use the validate_etw_input tool to validate both inputs together once collected.""",
            tools=[validate_etw_input]
        )

        self.provider_guid: Optional[str] = None
        self.rule_id: Optional[str] = None

    async def collect_inputs(
        self,
        provider_guid: Optional[str] = None,
        rule_id: Optional[str] = None
    ) -> ETWInputData:
        """
        Collect and validate ETW inputs through a conversational flow.

        Args:
            provider_guid: Pre-populated provider GUID (optional, for automation)
            rule_id: Pre-populated rule ID (optional, for automation)

        Returns:
            ETWInputData with validated inputs

        Raises:
            ValueError: If inputs are invalid after validation
        """
        # If both inputs are pre-populated, validate and return directly
        if provider_guid is not None and rule_id is not None:
            guid_valid, guid_error = validate_provider_guid(provider_guid)
            if not guid_valid:
                raise ValueError(guid_error)

            rule_valid, rule_error = validate_rule_id(rule_id)
            if not rule_valid:
                raise ValueError(rule_error)

            return ETWInputData(provider_guid=provider_guid, rule_id=rule_id)

        # Start conversational collection
        initial_prompt = "Hello! I need to collect ETW information for your detector. Let's get started."
        response = await self.agent.run(initial_prompt)

        print(f"\n🤖 Agent: {response}\n")

        # Conversational loop for collecting inputs
        max_attempts = 3
        attempts = 0

        while attempts < max_attempts:
            # Collect provider GUID
            if not self.provider_guid:
                user_guid = input("You: ").strip()
                guid_valid, guid_error = validate_provider_guid(user_guid)

                if not guid_valid:
                    error_prompt = f"The provider GUID '{user_guid}' is invalid. {guid_error} Please try again."
                    response = await self.agent.run(error_prompt)
                    print(f"\n🤖 Agent: {response}\n")
                    attempts += 1
                    continue

                self.provider_guid = user_guid
                confirm_prompt = f"Great! I've recorded the provider GUID as {user_guid}. Now, please provide the rule ID for your detector."
                response = await self.agent.run(confirm_prompt)
                print(f"\n🤖 Agent: {response}\n")

            # Collect rule ID
            if not self.rule_id:
                user_rule = input("You: ").strip()
                rule_valid, rule_error = validate_rule_id(user_rule)

                if not rule_valid:
                    error_prompt = f"The rule ID '{user_rule}' is invalid. {rule_error} Please try again."
                    response = await self.agent.run(error_prompt)
                    print(f"\n🤖 Agent: {response}\n")
                    attempts += 1
                    continue

                self.rule_id = user_rule

                # Final validation using the agent's tool
                validation_prompt = f"Please validate these inputs: Provider GUID: {self.provider_guid}, Rule ID: {self.rule_id}"
                response = await self.agent.run(validation_prompt)
                print(f"\n🤖 Agent: {response}\n")

                # Success!
                return ETWInputData(
                    provider_guid=self.provider_guid,
                    rule_id=self.rule_id
                )

        # Max attempts reached
        raise ValueError(
            f"Failed to collect valid inputs after {max_attempts} attempts. "
            "Please ensure provider GUID is in UUID format and rule ID is not empty."
        )


async def create_etw_input_agent() -> ETWInputAgent:
    """
    Factory function to create an ETW Input Agent.

    Returns:
        Configured ETWInputAgent instance using Azure OpenAI
    """
    return ETWInputAgent()
