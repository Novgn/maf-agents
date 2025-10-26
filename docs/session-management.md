# Session Management Implementation

**Status**: ✅ Implemented and Integrated
**Last Updated**: 2025-01-26

## Quick Links

- [Setup Guide](./setup-session-storage.md) - Step-by-step Azure configuration
- [Integration Summary](./INTEGRATION_SUMMARY.md) - What was implemented
- [Test Script](../server/test_session_store.py) - Verify your setup

## Overview

Production-ready session management using Azure Table Storage for the maf-agents workflow system.

**Key Features**:
- ✅ Persistent session storage across server restarts
- ✅ Full conversation history tracking
- ✅ Automatic Azure authentication (CLI, Managed Identity, Service Principal)
- ✅ User-isolated sessions (ready for multi-tenant)
- ✅ Automatic cleanup for cost management
- ✅ Session restoration and resumption

## Architecture

### Azure Table Storage Schema

**Table Name**: `WorkflowSessions`

**Entity Structure**:
- **PartitionKey**: `user_id` - Enables efficient queries by user
- **RowKey**: `workflow_id` - Unique workflow identifier
- **Columns**:
  - `status`: Current workflow status (running, completed, failed)
  - `current_step`: Current workflow step number (1-9)
  - `created_at`: ISO timestamp of workflow creation
  - `updated_at`: ISO timestamp of last update
  - `conversation_history`: JSON array of chat messages
  - `workflow_data`: JSON object with workflow state
  - `metadata`: JSON object with user context and additional data

### Features Implemented

✅ **Automatic Authentication**
- Uses `DefaultAzureCredential` (supports Azure CLI, Managed Identity, Environment Variables)
- Production-ready authentication without hardcoded secrets

✅ **Session Persistence**
- Store and retrieve complete workflow state
- Conversation history tracking
- User context management

✅ **Query Capabilities**
- List all sessions for a user
- Retrieve specific workflow sessions
- Query by date range

✅ **Automatic Cleanup**
- Delete sessions older than N days
- Helps manage storage costs

✅ **Error Handling**
- Graceful handling of missing sessions
- Detailed logging
- Exception propagation with context

## Usage

### Setup

1. **Set Environment Variables**:
```bash
export AZURE_STORAGE_ENDPOINT="https://<your-account>.table.core.windows.net"
export AZURE_TABLE_NAME="WorkflowSessions"  # Optional, defaults to WorkflowSessions
```

2. **Authenticate with Azure**:
```bash
# Option 1: Azure CLI (Development)
az login

# Option 2: Managed Identity (Production)
# Automatically detected when running on Azure (App Service, Functions, etc.)

# Option 3: Service Principal (CI/CD)
export AZURE_CLIENT_ID="..."
export AZURE_CLIENT_SECRET="..."
export AZURE_TENANT_ID="..."
```

### Python Examples

#### Create Session Store

```python
from storage import create_session_store_from_env, WorkflowSession

# Initialize from environment variables
store = create_session_store_from_env()
```

#### Save a Session

```python
from datetime import datetime, timezone

session = WorkflowSession(
    workflow_id="workflow-123",
    user_id="user@example.com",
    status="running",
    current_step=1,
    created_at=datetime.now(timezone.utc).isoformat(),
    updated_at=datetime.now(timezone.utc).isoformat(),
    conversation_history=[
        {"role": "user", "content": "I want to detect suspicious PowerShell"},
        {"role": "assistant", "content": "Great! Let me help you..."}
    ],
    workflow_data={
        "provider_guid": "...",
        "rule_id": "..."
    },
    metadata={
        "user_email": "user@example.com",
        "session_start": "2025-01-26T10:00:00Z"
    }
)

await store.save_session(session)
```

#### Retrieve a Session

```python
session = await store.get_session(
    workflow_id="workflow-123",
    user_id="user@example.com"
)

if session:
    print(f"Workflow status: {session.status}")
    print(f"Current step: {session.current_step}")
    print(f"Chat history: {len(session.conversation_history)} messages")
```

#### List User Sessions

```python
sessions = await store.list_user_sessions(
    user_id="user@example.com",
    limit=50
)

for session in sessions:
    print(f"{session.workflow_id}: {session.status} (Step {session.current_step})")
```

#### Cleanup Old Sessions

```python
# Delete sessions older than 30 days
deleted_count = await store.cleanup_old_sessions(days=30)
print(f"Deleted {deleted_count} old sessions")
```

## Integration with FastAPI

### ✅ Completed Integration

The session store has been fully integrated into the FastAPI backend (`server/api/main.py`):

#### 1. **Session Store Initialization** ✅
- Session store initialized in `lifespan` function from environment variables
- Graceful fallback if Azure Table Storage is not configured
- Uses `DefaultAzureCredential` for authentication

**Code**: `server/api/main.py:40-56`

#### 2. **Workflow Creation** ✅
- Creates initial session in Azure Table Storage when workflow is created
- Stores workflow metadata (created_at, status, user_id)
- Uses placeholder `user_id="anonymous"` until Azure AD auth is implemented

**Code**: `server/api/main.py:259-280`

#### 3. **Session Updates During Workflow Execution** ✅
- Automatically saves session updates as workflow progresses
- Updates status (running → completed/failed)
- Saves workflow data and error messages
- Tracks current step number

**Code**: `server/api/main.py:147-232`

#### 4. **Conversation History Persistence** ✅
- Saves user messages when submitted via `/api/workflows/{id}/input`
- Saves agent responses when broadcast via WebSocket
- Includes timestamps for all messages
- Maintains conversation continuity across server restarts

**Code**:
- User messages: `server/api/main.py:389-402`
- Agent messages: `server/api/main.py:251-267`

#### 5. **Session Restoration** ✅
- Restores session from Azure Table Storage if not in memory
- Automatically called when fetching workflow status
- Enables resuming workflows after server restart

**Code**: `server/api/main.py:369-396`

#### 6. **Session Management Endpoints** ✅

**List User Sessions**: `GET /api/sessions?user_id=anonymous&limit=100`
- Returns all sessions for a user with conversation history
- Sorted by most recently updated
- Code: `server/api/main.py:498-537`

**Cleanup Old Sessions**: `POST /api/sessions/cleanup?days=30`
- Deletes sessions older than specified days
- Returns count of deleted sessions
- Code: `server/api/main.py:540-565`

### 🔄 Pending Integration Tasks

1. **Add User Authentication** (Next Task):
   - Replace `user_id="anonymous"` with actual user ID from JWT token
   - Extract user ID from Azure AD authentication
   - Associate workflows with authenticated users
   - Enable user-isolated session queries

2. **Session Resumption UI** (Future):
   - Add frontend component to list previous sessions
   - Allow users to resume incomplete workflows
   - Display conversation history from resumed sessions

## Security Considerations

✅ **No Secrets in Code**
- Uses Azure AD authentication
- Credentials managed by Azure platform

✅ **User Isolation**
- PartitionKey ensures users can only access their own sessions
- Can add additional RBAC checks

✅ **Data Encryption**
- Data encrypted at rest by Azure Storage
- Data encrypted in transit (HTTPS)

## Cost Considerations

**Azure Table Storage Pricing** (as of 2025):
- **Storage**: ~$0.045/GB per month
- **Transactions**: ~$0.00036 per 10,000 transactions

**Example Calculation**:
- 1,000 users
- 10 workflows per user per month
- 20 messages per workflow
- ~50KB per session

**Monthly Cost**:
- Storage: ~500MB = $0.02
- Transactions: ~200,000 = $0.01
- **Total**: ~$0.03/month

💡 **Tip**: Enable automatic cleanup to keep costs minimal.

## Monitoring

### Recommended Metrics

- Session creation rate
- Session retrieval latency
- Failed authentication attempts
- Storage size growth
- Old session cleanup effectiveness

### Azure Monitor Integration

```python
# Add Application Insights logging
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string="InstrumentationKey=..."
))

# Log session operations
logger.info(f"Session saved: {workflow_id}", extra={"custom_dimensions": {
    "user_id": user_id,
    "status": status,
    "step": current_step
}})
```

## Testing

### Unit Tests

```python
import pytest
from storage import AzureTableSessionStore, WorkflowSession

@pytest.mark.asyncio
async def test_save_and_retrieve_session():
    store = AzureTableSessionStore(
        endpoint=os.getenv("AZURE_STORAGE_ENDPOINT")
    )

    session = WorkflowSession(
        workflow_id="test-123",
        user_id="test-user",
        status="running",
        current_step=1,
        # ... other fields
    )

    await store.save_session(session)
    retrieved = await store.get_session("test-123", "test-user")

    assert retrieved.status == "running"
    assert retrieved.current_step == 1
```

### Integration Tests

Run against Azure Table Storage Emulator (Azurite):

```bash
# Start Azurite
docker run -p 10002:10002 mcr.microsoft.com/azure-storage/azurite \
    azurite-table --tableHost 0.0.0.0

# Set test endpoint
export AZURE_STORAGE_ENDPOINT="http://127.0.0.1:10002/devstoreaccount1"

# Run tests
pytest tests/test_session_store.py
```

## Migration from LocalStorage

### Current State (Frontend LocalStorage)
- Sessions stored in browser
- Lost on browser clear
- No cross-device support
- No user isolation

### New State (Azure Table Storage)
- Sessions stored in cloud
- Persistent across devices
- Multi-device support
- User-isolated sessions
- Queryable and analyzable

### Migration Steps

1. **Phase 1**: Dual-write (LocalStorage + Azure)
2. **Phase 2**: Read from Azure, fallback to LocalStorage
3. **Phase 3**: Azure only, remove LocalStorage code

## References

- [Azure Table Storage Python SDK](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/tables/azure-data-tables)
- [DefaultAzureCredential Authentication](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential)
- [Azure Table Storage Best Practices](https://learn.microsoft.com/en-us/azure/storage/tables/table-storage-design)
