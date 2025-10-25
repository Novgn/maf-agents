# Azure Services Setup Guide

**Document Version**: 1.0
**Date**: 2025-10-25
**Purpose**: Complete guide for setting up required Azure services for maf-agents

---

## Overview

maf-agents requires the following Azure services:

1. **Azure DevOps / Azure Repos** - Source control, PR management
2. **Azure Kusto (Azure Data Explorer)** - ETW schema discovery, results analysis
3. **Azure Active Directory (Microsoft Entra ID)** - Service principal authentication
4. **Azure Key Vault** (Optional) - Secrets management
5. **File Storage** - Checkpoint persistence (local filesystem for POC)

---

## Prerequisites

- Azure subscription with appropriate permissions
- Azure CLI installed (`az` command)
- Azure DevOps organization
- Owner or Contributor role on subscription

---

## Step 1: Azure Service Principal Setup

### Create Service Principal

```bash
# Log in to Azure
az login

# Set your subscription
az account set --subscription "{subscription-id}"

# Create service principal for maf-agents
az ad sp create-for-rbac \
  --name "maf-agents-poc" \
  --role Contributor \
  --scopes /subscriptions/{subscription-id}
```

**Output** (save these values):
```json
{
  "appId": "00000000-0000-0000-0000-000000000000",
  "displayName": "maf-agents-poc",
  "password": "your-client-secret",
  "tenant": "00000000-0000-0000-0000-000000000000"
}
```

### Assign Additional Permissions

#### Azure DevOps Permissions

1. Navigate to Azure DevOps → Organization Settings → Users
2. Add service principal as user
3. Grant permissions:
   - **Project**: Contributor
   - **Repos**: Read & Write
   - **Pull Requests**: Contribute to pull requests

Alternatively, use Azure DevOps CLI:

```bash
# Install Azure DevOps extension
az extension add --name azure-devops

# Set organization
az devops configure --defaults organization=https://dev.azure.com/{org}

# Add service principal to project
az devops user add \
  --email-id {service-principal-app-id}@{tenant-id} \
  --license-type stakeholder \
  --org https://dev.azure.com/{org}
```

#### Azure Kusto Permissions

```bash
# Get service principal object ID
SP_OBJECT_ID=$(az ad sp show --id {app-id} --query id -o tsv)

# Grant Kusto database viewer role
az kusto database-principal-assignment create \
  --cluster-name {cluster-name} \
  --database-name {database-name} \
  --resource-group {resource-group} \
  --principal-id $SP_OBJECT_ID \
  --principal-type App \
  --role Viewer \
  --principal-assignment-name maf-agents-viewer
```

---

## Step 2: Azure Kusto (Data Explorer) Setup

### Create Kusto Cluster (if needed)

```bash
# Create resource group
az group create \
  --name maf-agents-rg \
  --location eastus

# Create Kusto cluster (this may take 10-15 minutes)
az kusto cluster create \
  --cluster-name maf-agents-kusto \
  --resource-group maf-agents-rg \
  --location eastus \
  --sku name=Dev(No SLA)_Standard_E2a_v4 tier=Basic capacity=1
```

### Create Database

```bash
# Create database
az kusto database create \
  --cluster-name maf-agents-kusto \
  --database-name DetectorDev \
  --resource-group maf-agents-rg \
  --soft-delete-period P365D \
  --hot-cache-period P31D
```

### Configure Database Permissions

```bash
# Grant service principal database viewer permissions
az kusto database-principal-assignment create \
  --cluster-name maf-agents-kusto \
  --database-name DetectorDev \
  --resource-group maf-agents-rg \
  --principal-id {service-principal-object-id} \
  --principal-type App \
  --role Viewer \
  --principal-assignment-name maf-agents-poc-access
```

### Test Kusto Connection

```bash
# Get cluster URI
az kusto cluster show \
  --cluster-name maf-agents-kusto \
  --resource-group maf-agents-rg \
  --query uri -o tsv
```

**Output**: `https://maf-agents-kusto.eastus.kusto.windows.net`

---

## Step 3: Azure DevOps / Azure Repos Setup

### Create Azure DevOps Organization (if needed)

1. Navigate to https://dev.azure.com
2. Click "Create new organization"
3. Follow the wizard to create organization

### Create Project

```bash
# Create new project
az devops project create \
  --name maf-agents-poc \
  --org https://dev.azure.com/{org} \
  --visibility private
```

### Create Repository

```bash
# Create repository
az repos create \
  --name detector-development \
  --project maf-agents-poc \
  --org https://dev.azure.com/{org}
```

### Grant Service Principal Access

```bash
# Add service principal to project
az devops user add \
  --email-id {app-id}@{tenant-id} \
  --license-type stakeholder \
  --project maf-agents-poc \
  --org https://dev.azure.com/{org}

# Grant Contributor permissions
az devops security group membership add \
  --group-id "[maf-agents-poc]\\Contributors" \
  --member-id {service-principal-object-id} \
  --org https://dev.azure.com/{org}
```

### Test Azure Repos Connection

```bash
# List repositories
az repos list \
  --project maf-agents-poc \
  --org https://dev.azure.com/{org}
```

---

## Step 4: Azure Key Vault Setup (Optional)

### Create Key Vault

```bash
# Create Key Vault
az keyvault create \
  --name maf-agents-kv \
  --resource-group maf-agents-rg \
  --location eastus
```

### Grant Service Principal Access

```bash
# Grant secret read permissions to service principal
az keyvault set-policy \
  --name maf-agents-kv \
  --resource-group maf-agents-rg \
  --object-id {service-principal-object-id} \
  --secret-permissions get list
```

### Store Secrets

```bash
# Store tenant ID
az keyvault secret set \
  --vault-name maf-agents-kv \
  --name tenant-id \
  --value {tenant-id}

# Store client ID
az keyvault secret set \
  --vault-name maf-agents-kv \
  --name client-id \
  --value {app-id}

# Store client secret
az keyvault secret set \
  --vault-name maf-agents-kv \
  --name client-secret \
  --value {client-secret}
```

---

## Step 5: Environment Configuration

### Create .env File

Create `.env` file in project root:

```env
# Azure Authentication
AZURE_TENANT_ID={tenant-id}
AZURE_CLIENT_ID={app-id}
AZURE_CLIENT_SECRET={client-secret}

# Azure Key Vault (if using)
AZURE_KEY_VAULT_URL=https://maf-agents-kv.vault.azure.net/

# Azure Kusto
KUSTO_CLUSTER_URL=https://maf-agents-kusto.eastus.kusto.windows.net
KUSTO_DATABASE_NAME=DetectorDev

# Azure DevOps
AZURE_DEVOPS_ORG=https://dev.azure.com/{org}
AZURE_DEVOPS_PROJECT=maf-agents-poc
AZURE_DEVOPS_REPO=detector-development

# Optional: Auto-confirm results for testing
# MAF_AUTO_CONFIRM_RESULTS=false
```

### Secure .env File

```bash
# Add .env to .gitignore
echo ".env" >> .gitignore

# Set restrictive permissions
chmod 600 .env
```

---

## Step 6: Verification

### Test Authentication

```python
# Test script: test_auth.py
from shared.auth import get_auth_manager
from shared.config import get_config

config = get_config()
auth_mgr = get_auth_manager()

# Test Azure DevOps connection
connection = auth_mgr.get_azure_devops_connection(config.azure.azure_devops_org)
print(f"✓ Azure DevOps connection successful")

# Test Kusto connection
kusto_token = auth_mgr.get_kusto_token(config.azure.kusto_cluster_url)
print(f"✓ Kusto authentication successful")
```

Run test:
```bash
uv run python test_auth.py
```

### Test Kusto Query

```python
# Test script: test_kusto.py
from shared.kusto_client import create_kusto_client
from shared.auth import get_auth_manager
from shared.config import get_config

config = get_config()
auth_mgr = get_auth_manager()

kusto_client = create_kusto_client(
    cluster_url=config.azure.kusto_cluster_url,
    database=config.azure.kusto_database_name,
    auth_manager=auth_mgr
)

# Test query
query = "print 'Hello from Kusto!'"
results = kusto_client.execute_query(query)
print(f"✓ Kusto query successful: {results}")
```

Run test:
```bash
uv run python test_kusto.py
```

### Test Azure Repos

```python
# Test script: test_repos.py
from shared.auth import get_auth_manager
from shared.config import get_config

config = get_config()
auth_mgr = get_auth_manager()

connection = auth_mgr.get_azure_devops_connection(config.azure.azure_devops_org)
git_client = connection.clients.get_git_client()

# List repositories
repos = git_client.get_repositories(config.azure.azure_devops_project)
print(f"✓ Found {len(repos)} repositories")
for repo in repos:
    print(f"  - {repo.name}")
```

Run test:
```bash
uv run python test_repos.py
```

---

## Step 7: Test Data Preparation

### Create Historical PRs

For pattern learning, the system needs 20-30 historical detector PRs in the repository.

#### Option 1: Import from Existing Repository

```bash
# Clone existing detector repository
git clone https://dev.azure.com/{org}/{project}/_git/{existing-repo}

# Push to new repository
cd {existing-repo}
git remote add new-origin https://dev.azure.com/{org}/maf-agents-poc/_git/detector-development
git push new-origin --all
```

#### Option 2: Create Sample PRs

Create sample PRs manually:

1. Create branch: `detector/sample-detector-1`
2. Add detector files following your team's conventions
3. Create PR with descriptive title and description
4. Merge PR
5. Repeat 20-30 times with variations

### Load Test Data into Kusto

```kusto
// Create sample ETW schema table
.create table ETWSchema (
    ProviderGuid: string,
    EventId: int,
    FieldName: string,
    FieldType: string,
    Description: string
)

// Load sample data
.ingest inline into table ETWSchema <|
12345678-1234-1234-1234-123456789012,1,ProcessId,int,Process identifier
12345678-1234-1234-1234-123456789012,1,ProcessName,string,Process name
12345678-1234-1234-1234-123456789012,1,CommandLine,string,Command line arguments
```

---

## Troubleshooting

### Service Principal Authentication Fails

**Error**: `AADSTS700016: Application not found in directory`

**Solution**:
1. Verify tenant ID is correct
2. Ensure service principal exists: `az ad sp show --id {app-id}`
3. Check service principal isn't expired

### Kusto Access Denied

**Error**: `Principal is not authorized to access`

**Solution**:
1. Verify service principal has Viewer role on database
2. Check permissions: `az kusto database-principal-assignment list`
3. Wait 5-10 minutes for permissions to propagate

### Azure DevOps 401 Unauthorized

**Error**: `TF401027: You need the Git 'GenericContribute' permission`

**Solution**:
1. Verify service principal added to project
2. Check permission level (should be Contributor)
3. Ensure PAT token has correct scopes if using PAT instead of service principal

### Connection Timeout

**Error**: `Request timeout after 30 seconds`

**Solution**:
1. Check network connectivity
2. Verify firewall rules allow outbound HTTPS
3. Test connectivity: `curl -I https://{cluster}.kusto.windows.net`

---

## Cost Estimation

| Resource | Tier | Estimated Monthly Cost |
|----------|------|------------------------|
| Kusto Cluster | Dev(No SLA) E2a_v4 | $150-200 |
| Azure DevOps | Basic (5 users) | Free |
| Azure Key Vault | Standard | $0.03 per 10K ops |
| **Total** | | **~$150-200/month** |

**Note**: Dev tier Kusto is intended for non-production use. Production would use Standard tier ($500+/month).

---

## Security Checklist

- [ ] Service principal has minimum required permissions
- [ ] Secrets stored in Key Vault or .env (not in code)
- [ ] .env file added to .gitignore
- [ ] .env file has restrictive permissions (chmod 600)
- [ ] Service principal credentials rotated regularly (90 days)
- [ ] Audit logging enabled on Key Vault
- [ ] Network security rules configured (if using private endpoints)
- [ ] Multi-factor authentication enabled for admin accounts

---

## Next Steps

1. **Verify Setup**: Run all test scripts above
2. **Load Test Data**: Create historical PRs and Kusto test data
3. **Run Workflow**: Execute `uv run python workflows/detector_workflow.py`
4. **Monitor**: Check Azure Portal for resource usage
5. **Troubleshoot**: Refer to README troubleshooting section if issues arise

---

## Additional Resources

- [Azure Service Principal Documentation](https://learn.microsoft.com/en-us/entra/identity-platform/app-objects-and-service-principals)
- [Azure Kusto Quick Start](https://learn.microsoft.com/en-us/azure/data-explorer/create-cluster-and-database)
- [Azure DevOps Service Principal Authentication](https://learn.microsoft.com/en-us/azure/devops/integrate/get-started/authentication/service-principal-managed-identity)
- [Azure Key Vault Best Practices](https://learn.microsoft.com/en-us/azure/key-vault/general/best-practices)

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-25 | Dev Agent | Initial Azure setup guide created |
