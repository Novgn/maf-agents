"""
Unit tests for the authentication module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.keyvault.secrets import SecretClient

from shared.auth import AuthenticationManager, get_auth_manager


class TestAuthenticationManager:
    """Tests for AuthenticationManager class."""

    def test_init_with_default_credential(self):
        """Test initialization with DefaultAzureCredential."""
        with patch("shared.auth.DefaultAzureCredential") as mock_cred:
            auth_mgr = AuthenticationManager(use_default_credential=True)
            assert auth_mgr.use_default_credential is True
            mock_cred.assert_called_once()

    def test_init_with_client_secret_credential(self):
        """Test initialization with ClientSecretCredential."""
        with patch("shared.auth.ClientSecretCredential") as mock_cred:
            auth_mgr = AuthenticationManager(
                tenant_id="tenant-123",
                client_id="client-456",
                client_secret="secret-789",
                use_default_credential=False,
            )
            assert auth_mgr.use_default_credential is False
            mock_cred.assert_called_once_with(
                tenant_id="tenant-123",
                client_id="client-456",
                client_secret="secret-789",
            )

    def test_init_with_key_vault_url(self):
        """Test initialization with Key Vault URL."""
        with patch("shared.auth.DefaultAzureCredential"), patch(
            "shared.auth.SecretClient"
        ) as mock_secret_client:
            auth_mgr = AuthenticationManager(
                key_vault_url="https://test-vault.vault.azure.net/",
                use_default_credential=True,
            )
            assert auth_mgr.key_vault_url == "https://test-vault.vault.azure.net/"
            mock_secret_client.assert_called_once()

    def test_get_secret_success(self):
        """Test successful secret retrieval from Key Vault."""
        mock_secret = Mock()
        mock_secret.value = "test-secret-value"

        with patch("shared.auth.DefaultAzureCredential"), patch(
            "shared.auth.SecretClient"
        ) as mock_secret_client_class:
            mock_secret_client = Mock()
            mock_secret_client.get_secret.return_value = mock_secret
            mock_secret_client_class.return_value = mock_secret_client

            auth_mgr = AuthenticationManager(
                key_vault_url="https://test-vault.vault.azure.net/",
                use_default_credential=True,
            )

            secret_value = auth_mgr.get_secret("test-secret")
            assert secret_value == "test-secret-value"
            mock_secret_client.get_secret.assert_called_once_with("test-secret")

    def test_get_secret_no_key_vault(self):
        """Test get_secret raises error when Key Vault client is not initialized."""
        with patch("shared.auth.DefaultAzureCredential"):
            auth_mgr = AuthenticationManager(use_default_credential=True)

            with pytest.raises(ValueError, match="Key Vault client not initialized"):
                auth_mgr.get_secret("test-secret")

    def test_get_kusto_client(self):
        """Test Kusto client creation."""
        with patch("shared.auth.DefaultAzureCredential"), patch(
            "shared.auth.KustoClient"
        ) as mock_kusto_client, patch(
            "shared.auth.KustoConnectionStringBuilder.with_azure_token_credential"
        ) as mock_kcsb:
            auth_mgr = AuthenticationManager(use_default_credential=True)

            cluster_url = "https://test-cluster.region.kusto.windows.net"
            database = "test-database"

            client = auth_mgr.get_kusto_client(cluster_url, database)

            mock_kcsb.assert_called_once()
            mock_kusto_client.assert_called_once()

    def test_get_azure_devops_connection(self):
        """Test Azure DevOps connection creation."""
        mock_token = Mock()
        mock_token.token = "test-access-token"

        with patch("shared.auth.DefaultAzureCredential") as mock_cred_class, patch(
            "shared.auth.Connection"
        ) as mock_connection, patch(
            "shared.auth.BasicAuthentication"
        ) as mock_basic_auth:
            mock_cred = Mock()
            mock_cred.get_token.return_value = mock_token
            mock_cred_class.return_value = mock_cred

            auth_mgr = AuthenticationManager(use_default_credential=True)

            org_url = "https://dev.azure.com/test-org"
            connection = auth_mgr.get_azure_devops_connection(org_url)

            mock_cred.get_token.assert_called_once()
            mock_basic_auth.assert_called_once_with("", "test-access-token")
            mock_connection.assert_called_once()

    def test_credential_property(self):
        """Test credential property returns the credential object."""
        with patch("shared.auth.DefaultAzureCredential") as mock_cred_class:
            mock_cred = Mock()
            mock_cred_class.return_value = mock_cred

            auth_mgr = AuthenticationManager(use_default_credential=True)

            assert auth_mgr.credential == mock_cred


class TestGetAuthManager:
    """Tests for get_auth_manager factory function."""

    def test_factory_function(self):
        """Test factory function creates AuthenticationManager."""
        with patch("shared.auth.DefaultAzureCredential"):
            auth_mgr = get_auth_manager(use_default_credential=True)
            assert isinstance(auth_mgr, AuthenticationManager)
            assert auth_mgr.use_default_credential is True

    def test_factory_function_with_key_vault(self):
        """Test factory function with Key Vault URL."""
        with patch("shared.auth.DefaultAzureCredential"), patch(
            "shared.auth.SecretClient"
        ):
            auth_mgr = get_auth_manager(
                key_vault_url="https://test-vault.vault.azure.net/",
                use_default_credential=True,
            )
            assert auth_mgr.key_vault_url == "https://test-vault.vault.azure.net/"
