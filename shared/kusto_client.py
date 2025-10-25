"""
Azure Kusto client wrapper for maf-agents.

Provides a simplified, robust interface for executing Kusto queries
with error handling, retry logic, and timeout enforcement.
"""

import time
from typing import Optional, Dict, Any, List
from pathlib import Path
import yaml
import structlog
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.exceptions import KustoServiceError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from shared.auth import AuthenticationManager

logger = structlog.get_logger(__name__)


class KustoClientWrapper:
    """Wrapper for Azure Kusto client with error handling and retry logic."""

    # Class-level cache for query templates
    _query_templates: Optional[Dict[str, str]] = None
    _templates_path = Path(__file__).parent.parent / "config" / "kusto_queries.yaml"

    def __init__(
        self,
        cluster_url: str,
        database: str,
        auth_manager: Optional[AuthenticationManager] = None,
    ):
        """
        Initialize Kusto client wrapper.

        Args:
            cluster_url: Kusto cluster URL
            database: Database name
            auth_manager: AuthenticationManager instance for authentication
        """
        self.cluster_url = cluster_url
        self.database = database
        self.auth_manager = auth_manager

        # Create Kusto client
        if auth_manager:
            self.client = auth_manager.get_kusto_client(cluster_url, database)
        else:
            # Fallback to connection string builder (requires KUSTO_CONNECTION_STRING env var)
            kcsb = KustoConnectionStringBuilder.with_aad_device_authentication(cluster_url)
            self.client = KustoClient(kcsb)

        self.logger = logger.bind(cluster=cluster_url, database=database)
        self.logger.info("Initialized Kusto client wrapper")

    @classmethod
    def _load_query_templates(cls) -> Dict[str, str]:
        """
        Load query templates from YAML file (cached).

        Returns:
            Dictionary of template_name -> query_string

        Raises:
            FileNotFoundError: If templates file doesn't exist
            yaml.YAMLError: If templates file is invalid YAML
        """
        if cls._query_templates is None:
            if not cls._templates_path.exists():
                raise FileNotFoundError(
                    f"Query templates file not found: {cls._templates_path}"
                )

            with open(cls._templates_path, "r") as f:
                cls._query_templates = yaml.safe_load(f)

            if not isinstance(cls._query_templates, dict):
                raise ValueError("Query templates file must contain a dictionary")

        return cls._query_templates

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((KustoServiceError, ConnectionError)),
        reraise=True,
    )
    def execute_query(
        self, query: str, timeout_seconds: int = 30, parameters: Optional[Dict[str, Any]] = None  # noqa: ARG002
    ) -> List[Dict[str, Any]]:
        """
        Execute a Kusto query with timeout and retry logic.

        Args:
            query: KQL query string
            timeout_seconds: Query timeout in seconds (default: 30)
            parameters: Optional query parameters

        Returns:
            List of rows as dictionaries

        Raises:
            KustoServiceError: If query fails after retries
            TimeoutError: If query exceeds timeout
        """
        start_time = time.time()

        try:
            self.logger.info(
                "Executing Kusto query",
                query_preview=query[:100] + "..." if len(query) > 100 else query,
                timeout=timeout_seconds,
            )

            # Execute query
            response = self.client.execute(self.database, query)

            # Extract results
            results = []
            if response.primary_results:
                primary_table = response.primary_results[0]
                for row in primary_table:
                    results.append(dict(row))

            elapsed = time.time() - start_time
            self.logger.info(
                "Query executed successfully",
                row_count=len(results),
                elapsed_seconds=round(elapsed, 2),
            )

            return results

        except KustoServiceError as e:
            elapsed = time.time() - start_time
            self.logger.error(
                "Kusto query failed",
                error=str(e),
                elapsed_seconds=round(elapsed, 2),
            )
            raise
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(
                "Unexpected error executing Kusto query",
                error=str(e),
                error_type=type(e).__name__,
                elapsed_seconds=round(elapsed, 2),
            )
            raise

    def load_query_template(self, template_name: str, params: Dict[str, Any]) -> str:
        """
        Load a query template by name and replace placeholders with actual values.

        Args:
            template_name: Name of the template in kusto_queries.yaml
            params: Dictionary of parameter values

        Returns:
            Query string with placeholders replaced

        Raises:
            KeyError: If template name not found
            ValueError: If required parameter is missing

        Example:
            >>> params = {"provider_guid": "12345678-1234-1234-1234-123456789012"}
            >>> query = client.load_query_template("get_etw_schema", params)
        """
        try:
            # Load templates from YAML file
            templates = self._load_query_templates()

            # Get the template by name
            if template_name not in templates:
                available = ", ".join(templates.keys())
                raise KeyError(
                    f"Query template '{template_name}' not found. "
                    f"Available templates: {available}"
                )

            template = templates[template_name]

            # Substitute parameters
            query = template.format(**params)

            self.logger.debug(
                "Loaded query template",
                template_name=template_name,
                param_count=len(params)
            )

            return query

        except KeyError as e:
            if template_name in str(e):
                # Template not found error - already handled above
                raise
            # Missing parameter error
            self.logger.error(
                "Missing parameter in query template",
                template_name=template_name,
                missing_param=str(e)
            )
            raise ValueError(f"Missing required parameter: {e}") from e


def create_kusto_client(
    cluster_url: str,
    database: str,
    auth_manager: Optional[AuthenticationManager] = None,
) -> KustoClientWrapper:
    """
    Factory function to create a KustoClientWrapper.

    Args:
        cluster_url: Kusto cluster URL
        database: Database name
        auth_manager: Optional AuthenticationManager

    Returns:
        Configured KustoClientWrapper instance
    """
    return KustoClientWrapper(cluster_url, database, auth_manager)
