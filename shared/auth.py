"""
Authentication module for Azure services.

Provides authentication helpers for accessing Azure Repos, Azure Kusto,
and other Azure services using Azure AD service principals.
"""

import os
from typing import Optional

from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
import structlog

logger = structlog.get_logger(__name__)


class AuthenticationManager:
    """Manages authentication to Azure services."""

    def __init__(
        self,
        key_vault_url: Optional[str] = None,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        use_default_credential: bool = True,
    ):
        """
        Initialize the authentication manager.

        Args:
            key_vault_url: URL of the Azure Key Vault (e.g., https://myvault.vault.azure.net/)
            tenant_id: Azure AD tenant ID
            client_id: Service principal client ID
            client_secret: Service principal client secret
            use_default_credential: If True, use DefaultAzureCredential; otherwise use ClientSecretCredential

        If service principal credentials are not provided, they will be retrieved from Key Vault.
        If Key Vault URL is not provided, it will be read from AZURE_KEY_VAULT_URL environment variable.
        """
        self.key_vault_url = key_vault_url or os.getenv("AZURE_KEY_VAULT_URL")
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.use_default_credential = use_default_credential

        # Initialize credential
        self._credential = self._get_credential()

        # Initialize Key Vault client if URL is provided
        self._secret_client: Optional[SecretClient] = None
        if self.key_vault_url:
            self._secret_client = SecretClient(
                vault_url=self.key_vault_url, credential=self._credential
            )
            logger.info("Initialized Key Vault client", vault_url=self.key_vault_url)

    def _get_credential(self):
        """
        Get Azure credential based on configuration.

        Returns:
            Azure credential object (DefaultAzureCredential or ClientSecretCredential)
        """
        if self.use_default_credential:
            logger.info("Using DefaultAzureCredential for authentication")
            return DefaultAzureCredential()

        if not all([self.tenant_id, self.client_id, self.client_secret]):
            # Try to load from Key Vault
            if self.key_vault_url:
                logger.info("Loading service principal credentials from Key Vault")
                return self._get_credential_from_key_vault()
            else:
                raise ValueError(
                    "Service principal credentials or Key Vault URL must be provided"
                )

        logger.info(
            "Using ClientSecretCredential for authentication", client_id=self.client_id
        )
        return ClientSecretCredential(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

    def _get_credential_from_key_vault(self) -> ClientSecretCredential:
        """
        Retrieve service principal credentials from Key Vault and create credential.

        Returns:
            ClientSecretCredential configured with credentials from Key Vault

        Raises:
            ValueError: If required secrets are not found in Key Vault
        """
        # Use DefaultAzureCredential to access Key Vault
        temp_credential = DefaultAzureCredential()
        secret_client = SecretClient(
            vault_url=self.key_vault_url, credential=temp_credential
        )

        try:
            tenant_id = secret_client.get_secret("tenant-id").value
            client_id = secret_client.get_secret("client-id").value
            client_secret = secret_client.get_secret("client-secret").value

            logger.info("Retrieved service principal credentials from Key Vault")

            return ClientSecretCredential(
                tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
            )
        except Exception as e:
            logger.error(
                "Failed to retrieve credentials from Key Vault", error=str(e)
            )
            raise ValueError(
                f"Failed to retrieve service principal credentials from Key Vault: {e}"
            )

    def get_secret(self, secret_name: str) -> str:
        """
        Retrieve a secret from Azure Key Vault.

        Args:
            secret_name: Name of the secret to retrieve

        Returns:
            Secret value as string

        Raises:
            ValueError: If Key Vault client is not initialized
        """
        if not self._secret_client:
            raise ValueError("Key Vault client not initialized. Provide key_vault_url.")

        try:
            secret = self._secret_client.get_secret(secret_name)
            logger.info("Retrieved secret from Key Vault", secret_name=secret_name)
            return secret.value
        except Exception as e:
            logger.error(
                "Failed to retrieve secret from Key Vault",
                secret_name=secret_name,
                error=str(e),
            )
            raise

    def get_kusto_client(self, cluster_url: str, database: str) -> KustoClient:
        """
        Create an authenticated Kusto client.

        Args:
            cluster_url: Kusto cluster URL (e.g., https://mycluster.region.kusto.windows.net)
            database: Kusto database name

        Returns:
            Authenticated KustoClient instance
        """
        kcsb = KustoConnectionStringBuilder.with_azure_token_credential(
            cluster_url, self._credential
        )

        client = KustoClient(kcsb)
        logger.info(
            "Created Kusto client",
            cluster_url=cluster_url,
            database=database,
        )
        return client

    def get_azure_devops_connection(self, organization_url: str) -> Connection:
        """
        Create an authenticated Azure DevOps connection.

        Args:
            organization_url: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)

        Returns:
            Authenticated Connection instance for Azure DevOps

        Note:
            Azure DevOps Python SDK currently uses PAT or OAuth for authentication.
            For service principal authentication, we need to obtain an access token
            and use it as a PAT equivalent.
        """
        # Get access token for Azure DevOps
        token = self._credential.get_token("499b84ac-1321-427f-aa17-267ca6975798/.default")

        # Create connection using the token
        credentials = BasicAuthentication("", token.token)
        connection = Connection(base_url=organization_url, creds=credentials)

        logger.info(
            "Created Azure DevOps connection", organization_url=organization_url
        )
        return connection

    @property
    def credential(self):
        """Get the Azure credential object."""
        return self._credential


def get_auth_manager(
    key_vault_url: Optional[str] = None,
    use_default_credential: bool = True,
) -> AuthenticationManager:
    """
    Factory function to create an AuthenticationManager instance.

    Args:
        key_vault_url: URL of the Azure Key Vault (optional, will use env var if not provided)
        use_default_credential: If True, use DefaultAzureCredential

    Returns:
        Configured AuthenticationManager instance
    """
    return AuthenticationManager(
        key_vault_url=key_vault_url,
        use_default_credential=use_default_credential,
    )
