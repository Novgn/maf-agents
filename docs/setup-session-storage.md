# Session Storage Setup Guide

This guide walks you through setting up Azure Table Storage for session management in maf-agents.

## Prerequisites

- Azure subscription
- Azure CLI installed (`az --version` to verify)
- Python environment with `uv` or `pip`

## Step 1: Install Azure SDK Dependencies

The required Azure SDK packages are already listed in `pyproject.toml`. Install them:

```bash
cd server
uv sync
```

Or if using pip:

```bash
pip install azure-data-tables azure-identity azure-core
```

## Step 2: Create Azure Storage Account

### Option A: Using Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource" → "Storage account"
3. Fill in the required fields:
   - **Resource group**: Create new or select existing
   - **Storage account name**: Choose a globally unique name (e.g., `mafagentsstorage`)
   - **Region**: Choose your preferred region
   - **Performance**: Standard (sufficient for Table Storage)
   - **Redundancy**: LRS (Locally Redundant Storage) is fine for dev/test
4. Click "Review + Create" → "Create"
5. Wait for deployment to complete

### Option B: Using Azure CLI

```bash
# Login to Azure
az login

# Create resource group (if you don't have one)
az group create --name maf-agents-rg --location eastus

# Create storage account
az storage account create \
  --name mafagentsstorage \
  --resource-group maf-agents-rg \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2

# Get the storage account endpoint
az storage account show \
  --name mafagentsstorage \
  --resource-group maf-agents-rg \
  --query "primaryEndpoints.table" \
  --output tsv
# Output: https://mafagentsstorage.table.core.windows.net/
```

## Step 3: Configure Authentication

The session store uses `DefaultAzureCredential` which supports multiple authentication methods.

### Development (Azure CLI)

Easiest for local development:

```bash
# Login to Azure CLI
az login

# Verify login
az account show
```

### Production (Managed Identity)

When deployed to Azure (App Service, Azure Functions, etc.), Managed Identity is automatically detected. No configuration needed!

### CI/CD (Service Principal)

For automated deployments:

```bash
# Set environment variables
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"
```

## Step 4: Grant Permissions

Your Azure identity (user, managed identity, or service principal) needs permissions to access the storage account.

### Using Azure Portal

1. Go to your storage account in Azure Portal
2. Click "Access Control (IAM)" in the left menu
3. Click "Add" → "Add role assignment"
4. Select role: **Storage Table Data Contributor**
5. Click "Next"
6. Select "User, group, or service principal"
7. Click "+ Select members"
8. Search for your user account or service principal
9. Click "Select" → "Review + assign"

### Using Azure CLI

```bash
# Get your current user's object ID
USER_ID=$(az ad signed-in-user show --query id --output tsv)

# Get storage account resource ID
STORAGE_ID=$(az storage account show \
  --name mafagentsstorage \
  --resource-group maf-agents-rg \
  --query id \
  --output tsv)

# Assign Storage Table Data Contributor role
az role assignment create \
  --assignee $USER_ID \
  --role "Storage Table Data Contributor" \
  --scope $STORAGE_ID

echo "✓ Permissions granted"
```

## Step 5: Configure Environment Variables

Update your `.env` file in the `server` directory:

```bash
cd server
cp .env.example .env
```

Edit `.env` and add:

```bash
# Azure Table Storage (for session management)
AZURE_STORAGE_ENDPOINT=https://mafagentsstorage.table.core.windows.net
AZURE_TABLE_NAME=WorkflowSessions
```

**Important**: Replace `mafagentsstorage` with your actual storage account name.

## Step 6: Test the Setup

Create a simple test script to verify everything works:

```python
# test_session_store.py
import asyncio
from storage import create_session_store_from_env, WorkflowSession
from datetime import datetime, timezone

async def test_session_store():
    # Initialize session store
    store = create_session_store_from_env()
    print("✓ Session store initialized")

    # Create a test session
    session = WorkflowSession(
        workflow_id="test-workflow-001",
        user_id="test-user",
        status="running",
        current_step=1,
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        conversation_history=[
            {"role": "user", "content": "Hello, I want to create a detector"},
            {"role": "assistant", "content": "Great! Let's get started..."}
        ],
        workflow_data={"test": "data"},
        metadata={"source": "test_script"}
    )

    # Save session
    await store.save_session(session)
    print("✓ Session saved")

    # Retrieve session
    retrieved = await store.get_session("test-workflow-001", "test-user")
    if retrieved:
        print(f"✓ Session retrieved: {retrieved.workflow_id}")
        print(f"  - Status: {retrieved.status}")
        print(f"  - Conversation messages: {len(retrieved.conversation_history)}")
    else:
        print("❌ Failed to retrieve session")

    # List sessions for user
    sessions = await store.list_user_sessions("test-user")
    print(f"✓ Found {len(sessions)} sessions for test-user")

    # Cleanup test session
    deleted = await store.delete_session("test-workflow-001", "test-user")
    print(f"✓ Test session deleted: {deleted}")

if __name__ == "__main__":
    asyncio.run(test_session_store())
```

Run the test:

```bash
cd server
python test_session_store.py
```

Expected output:

```
✓ Created table 'WorkflowSessions'
✓ Session store initialized
✓ Saved session: workflow=test-wor, user=test-user
✓ Session saved
✓ Session retrieved: test-workflow-001
  - Status: running
  - Conversation messages: 2
✓ Found 1 sessions for test-user
✓ Deleted session: workflow=test-wor, user=test-user
✓ Test session deleted: True
```

## Step 7: Verify in Azure Portal

1. Go to your storage account in Azure Portal
2. Click "Storage Browser" in the left menu
3. Click "Tables"
4. You should see the `WorkflowSessions` table
5. Click on the table to view entities

## Troubleshooting

### Error: "AZURE_STORAGE_ENDPOINT environment variable must be set"

**Solution**: Make sure you've set the `AZURE_STORAGE_ENDPOINT` in your `.env` file and that the file is in the `server` directory.

### Error: "Authentication failed"

**Solutions**:
- Verify you're logged in: `az login`
- Check your account: `az account show`
- Verify permissions: Go to storage account → Access Control (IAM) → Check assignments

### Error: "Storage account not found"

**Solutions**:
- Verify the storage account name in the endpoint URL
- Check the storage account exists: `az storage account show --name mafagentsstorage --resource-group maf-agents-rg`

### Error: "This request is not authorized to perform this operation"

**Solutions**:
- You need the "Storage Table Data Contributor" role (see Step 4)
- Wait a few minutes after granting permissions (propagation delay)

## Development vs Production

### Development
- Use Azure CLI authentication (`az login`)
- Set `AZURE_STORAGE_ENDPOINT` to your development storage account
- Single storage account shared by all developers is fine

### Production
- Use Managed Identity (no secrets needed!)
- Create separate storage accounts for staging/production
- Enable soft delete and point-in-time restore for data protection
- Set up monitoring and alerts

## Cost Optimization

Azure Table Storage is very cost-effective. To minimize costs:

1. **Use the cleanup endpoint** to delete old sessions:
   ```bash
   # Schedule this as a cron job or Azure Function
   curl -X POST http://localhost:8000/api/sessions/cleanup?days=30
   ```

2. **Monitor storage usage**:
   ```bash
   az storage account show-usage \
     --name mafagentsstorage \
     --resource-group maf-agents-rg
   ```

3. **Set up lifecycle management** (optional):
   - Go to storage account → Data management → Lifecycle management
   - Create a rule to delete entities older than X days

## Next Steps

- [Azure AD Authentication Setup](./setup-azure-ad-auth.md) (TODO)
- [Session Management Documentation](./session-management.md)
- [Deployment Guide](./deployment.md) (TODO)

## References

- [Azure Table Storage Overview](https://learn.microsoft.com/en-us/azure/storage/tables/table-storage-overview)
- [DefaultAzureCredential](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential)
- [Azure Table Storage Python SDK](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/tables/azure-data-tables)
