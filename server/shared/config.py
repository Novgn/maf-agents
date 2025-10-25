"""
Configuration management for maf-agents.

Loads configuration from environment variables and provides
typed configuration objects using Pydantic.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureConfig(BaseSettings):
    """Azure service configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Azure Key Vault
    azure_key_vault_url: Optional[str] = None

    # Azure Kusto (Data Explorer)
    kusto_cluster_url: Optional[str] = None
    kusto_database_name: Optional[str] = None

    # Azure DevOps / Azure Repos
    azure_devops_org: Optional[str] = None
    azure_devops_project: Optional[str] = None
    azure_devops_repo: Optional[str] = None

    # Azure Table Storage (for checkpoints)
    azure_storage_connection_string: Optional[str] = None
    checkpoint_table_name: str = "workflowcheckpoints"

    # Service Principal (optional - can be loaded from Key Vault)
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

    # Logging
    log_level: str = "INFO"


class AppConfig(BaseSettings):
    """Application-level configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = "maf-agents"
    app_version: str = "0.1.0"
    environment: str = "development"

    # Azure configuration
    azure: AzureConfig = AzureConfig()


def get_config() -> AppConfig:
    """
    Load and return application configuration.

    Returns:
        AppConfig instance with loaded configuration
    """
    return AppConfig()
