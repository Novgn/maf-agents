# Story 1.2: Azure Service Principal and Key Vault Configuration

**Epic**: Epic 1: Foundation & Workflow Orchestration

## User Story

As a **developer**,
I want **Azure authentication configured with service principal credentials stored in Azure Key Vault**,
so that **workflow agents can securely access Azure Repos and Azure Kusto**.

## Acceptance Criteria

1. Service principal created with appropriate RBAC roles for Azure Repos (Contributor) and Azure Kusto (Viewer)
2. Service principal credentials (tenant ID, client ID, client secret) stored in Azure Key Vault
3. `/shared/auth.py` module implements authentication helper using `DefaultAzureCredential` or `ClientSecretCredential`
4. Environment variables or config file specify Azure Key Vault URL and secret names
5. Authentication module retrieves credentials from Key Vault and returns authenticated clients for Azure Repos and Azure Kusto
6. Unit test validates successful authentication and credential retrieval (using test credentials or mocks)

## Notes

Security is critical from the start. This story establishes the authentication pattern that all agents will use to access Azure services.

## Related Documents

- PRD: docs/prd.md (Epic 1, Story 1.2)
- Architecture: docs/architecture.md
