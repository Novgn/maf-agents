"""
Kusto Schema Discovery Agent using Microsoft Agent Framework.

This module implements an agent that queries Kusto to discover existing detectors
and retrieve ETW schema definitions for a given provider GUID.
"""

from typing import Optional, List, Dict, Any

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient

from shared.models import KustoSchemaData, KustoSchemaField
from shared.kusto_client import KustoClientWrapper


class SchemaDiscoveryAgent:
    """
    Schema Discovery Agent using Microsoft Agent Framework.

    This agent queries Kusto to discover existing detectors and retrieve
    ETW schema definitions, presenting findings conversationally to the user.
    """

    def __init__(
        self,
        kusto_client: KustoClientWrapper,
    ):
        """
        Initialize the Schema Discovery Agent.

        Args:
            kusto_client: Kusto client wrapper for executing queries
        """
        self.kusto_client = kusto_client

        # Create the chat client
        chat_client = AzureOpenAIChatClient()

        # Create the conversational agent with tools
        # Note: We can't pass kusto_client directly to tools, so we'll use it in the methods
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="Schema Discovery Agent",
            instructions="""You are a helpful assistant that discovers ETW schema information
and existing detectors from Kusto. Your role is to:

1. Query Kusto to find existing detectors for a given ETW provider GUID
2. Query Kusto to retrieve the ETW schema definition
3. Present findings conversationally and clearly to the user

Be informative and highlight key findings like:
- How many existing detectors were found
- Names of existing detectors
- Number of schema fields discovered
- Key schema fields

Help the user understand what already exists in the system."""
        )

        self.provider_guid: Optional[str] = None
        self.existing_detectors: List[Dict[str, Any]] = []
        self.schema_fields: List[KustoSchemaField] = []

    async def discover_schema(
        self,
        provider_guid: str,
        rule_id: str  # noqa: ARG002
    ) -> KustoSchemaData:
        """
        Discover schema and existing detectors for the given provider GUID.

        Args:
            provider_guid: The ETW provider GUID
            rule_id: The rule ID (for context)

        Returns:
            KustoSchemaData with discovered information
        """
        self.provider_guid = provider_guid

        # Start conversational discovery
        initial_prompt = f"""I'm going to discover schema information for ETW provider GUID {provider_guid}.
Let me query Kusto to find existing detectors and the schema definition."""

        response = await self.agent.run(initial_prompt)
        print(f"\n🤖 Schema Discovery Agent: {response}\n")

        # Query for existing detectors
        try:
            detectors_query = self.kusto_client.load_query_template(
                "find_existing_detectors",
                {"provider_guid": provider_guid}
            )
            detector_results = self.kusto_client.execute_query(detectors_query, timeout_seconds=30)
            self.existing_detectors = detector_results
            existing_detector_names = [row.get("DetectorName", "Unknown") for row in detector_results]

            if existing_detector_names:
                detectors_summary = f"Found {len(existing_detector_names)} existing detector(s): {', '.join(existing_detector_names)}"
            else:
                detectors_summary = f"No existing detectors found for provider GUID {provider_guid}."

            print(f"   Existing Detectors: {detectors_summary}")

        except Exception as e:
            print(f"   ⚠️  Error querying existing detectors: {e}")
            existing_detector_names = []
            self.existing_detectors = []
            detectors_summary = f"Error querying existing detectors: {str(e)}"

        # Query for ETW schema
        try:
            schema_query = self.kusto_client.load_query_template(
                "get_etw_schema",
                {"provider_guid": provider_guid}
            )
            schema_results = self.kusto_client.execute_query(schema_query, timeout_seconds=30)
            self.schema_fields = [
                KustoSchemaField(
                    name=row.get("FieldName", "Unknown"),
                    data_type=row.get("DataType", "string"),
                    description=row.get("Description")
                )
                for row in schema_results
            ]

            field_names = [field.name for field in self.schema_fields]
            if field_names:
                schema_summary = f"Schema contains {len(field_names)} field(s): {', '.join(field_names[:5])}"
                if len(field_names) > 5:
                    schema_summary += f" and {len(field_names) - 5} more"
            else:
                schema_summary = f"No schema definition found for provider GUID {provider_guid}."

            print(f"   ETW Schema: {schema_summary}")

        except Exception as e:
            print(f"   ⚠️  Error querying ETW schema: {e}")
            self.schema_fields = []
            schema_summary = f"Error querying ETW schema: {str(e)}"

        # Present findings conversationally
        findings_prompt = f"""
Based on my queries:
- {detectors_summary}
- {schema_summary}

Please summarize what this means for the detector development."""

        findings_response = await self.agent.run(findings_prompt)
        print(f"\n🤖 Schema Discovery Agent: {findings_response}\n")

        # Create and return schema data
        schema_data = KustoSchemaData(
            provider_guid=provider_guid,
            schema_fields=self.schema_fields,
            existing_detectors=existing_detector_names
        )

        return schema_data


async def create_schema_discovery_agent(
    kusto_client: KustoClientWrapper,
) -> SchemaDiscoveryAgent:
    """
    Factory function to create a Schema Discovery Agent.

    Args:
        kusto_client: Kusto client wrapper for executing queries

    Returns:
        Configured SchemaDiscoveryAgent instance using Azure OpenAI
    """
    return SchemaDiscoveryAgent(kusto_client=kusto_client)
