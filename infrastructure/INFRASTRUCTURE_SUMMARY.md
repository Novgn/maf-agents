# Infrastructure Summary

**Created**: 2025-01-26
**Status**: ✅ Complete
**Purpose**: Production-ready Infrastructure as Code for MAF Agents application

---

## What Was Created

### Directory Structure

```
infrastructure/
├── main.bicep                      # Main orchestration template
├── modules/                        # Reusable Bicep modules
│   ├── identity.bicep              # User-Assigned Managed Identity
│   ├── storage.bicep               # Azure Table Storage
│   ├── monitoring.bicep            # Application Insights
│   ├── backend.bicep               # FastAPI App Service
│   └── frontend.bicep              # Next.js Static Web App
├── parameters/                     # Environment-specific parameters
│   ├── dev.bicepparam              # Development environment
│   └── prod.bicepparam             # Production environment
├── README.md                       # Comprehensive deployment guide
├── QUICKSTART.md                   # Quick start guide (10-minute deployment)
├── INFRASTRUCTURE_SUMMARY.md       # This file
└── .bicepignore                    # Files to exclude from Bicep builds
```

### Azure Resources Deployed

The `main.bicep` template deploys a complete, production-ready environment:

#### 1. **User-Assigned Managed Identity** (`modules/identity.bicep`)
- **Purpose**: Passwordless authentication for App Service
- **Access**: Storage Table Data Contributor role
- **Benefits**: No connection strings or secrets in code

#### 2. **Log Analytics Workspace**
- **Purpose**: Centralized logging for Application Insights
- **Retention**: 30 days
- **SKU**: PerGB2018 (pay-as-you-go)

#### 3. **Application Insights** (`modules/monitoring.bicep`)
- **Purpose**: Monitor application performance, errors, and telemetry
- **Type**: Web
- **Integration**: Linked to Log Analytics workspace

#### 4. **Azure Storage Account** (`modules/storage.bicep`)
- **Purpose**: Session management via Table Storage
- **Features**:
  - Table Storage for workflow sessions
  - Pre-creates `WorkflowSessions` table
  - HTTPS-only, TLS 1.2+
  - Encryption at rest
  - Role-based access via managed identity
- **SKUs**:
  - Dev: Standard_LRS
  - Prod: Standard_GRS (geo-redundant)

#### 5. **App Service Plan**
- **Purpose**: Hosts the FastAPI backend
- **Configuration**:
  - Linux-based
  - Python 3.11 runtime
- **SKUs**:
  - Dev: F1 (Free tier)
  - Staging: B1 (Basic)
  - Prod: P1V3 (Premium V3) with 2 instances

#### 6. **Backend App Service** (`modules/backend.bicep`)
- **Purpose**: FastAPI backend for agent workflows
- **Features**:
  - Managed identity authentication
  - WebSocket support
  - CORS enabled for frontend
  - Environment variables auto-configured:
    - `AZURE_STORAGE_ENDPOINT`
    - `AZURE_TABLE_NAME`
    - `AZURE_CLIENT_ID`
    - `APPLICATIONINSIGHTS_CONNECTION_STRING`
    - Azure DevOps integration (optional)
  - Health check endpoint: `/health`
  - Auto-generated API docs: `/docs`

#### 7. **Static Web App** (`modules/frontend.bicep`)
- **Purpose**: Next.js frontend with global CDN
- **Features**:
  - Automatic HTTPS
  - Built-in CI/CD (GitHub Actions or Azure DevOps)
  - Custom domain support
  - Environment variables:
    - `NEXT_PUBLIC_API_URL`
    - `NEXT_PUBLIC_WS_URL`
- **SKUs**:
  - Dev: Free
  - Staging/Prod: Standard

### Environment Configurations

| Resource | Development | Staging | Production |
|----------|------------|---------|------------|
| **App Service Plan** | F1 (Free) | B1 (Basic) | P1V3 (Premium V3, 2 instances) |
| **Storage** | Standard_LRS | Standard_LRS | Standard_GRS |
| **Static Web App** | Free | Standard | Standard |
| **Est. Monthly Cost** | $0-5 | $55 | $300 |

## Key Features

### 🔒 Security

1. **No Secrets in Code**
   - Managed identity for all Azure authentication
   - No connection strings or API keys stored in app settings

2. **Encryption**
   - HTTPS-only enforcement
   - TLS 1.2 minimum
   - Data encrypted at rest (Azure-managed keys)

3. **RBAC**
   - Least-privilege role assignments
   - Storage Table Data Contributor role scoped to storage account

4. **Network Security**
   - Configurable IP restrictions (see backend module)
   - Azure Services bypass for storage

### 🚀 Deployment

1. **Infrastructure as Code**
   - All resources defined in Bicep
   - Idempotent deployments
   - Version-controlled

2. **Environment Parity**
   - Same template for all environments
   - Parameter files for configuration
   - Consistent naming conventions

3. **Automated CI/CD Ready**
   - Static Web App auto-deploys from GitHub/Azure DevOps
   - Backend deployable via `az webapp deployment`
   - GitHub Actions examples included

### 📊 Monitoring

1. **Application Insights**
   - Performance metrics
   - Error tracking
   - Custom events and metrics
   - Log aggregation

2. **Health Checks**
   - Backend: `/health` endpoint
   - Automatic health check configuration

3. **Logging**
   - Centralized in Log Analytics
   - 30-day retention (configurable)

## Deployment Outputs

After successful deployment, the template provides these outputs:

```json
{
  "storageAccountName": "mafagentXXXXXXXXXX",
  "storageTableEndpoint": "https://mafagentXXXXXXXXXX.table.core.windows.net/",
  "backendApiUrl": "https://maf-agents-api-dev-XXXX.azurewebsites.net",
  "frontendUrl": "https://maf-agents-web-dev.azurestaticapps.net",
  "applicationInsightsConnectionString": "InstrumentationKey=...",
  "managedIdentityClientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "deploymentSummary": {
    "environment": "dev",
    "location": "eastus",
    "frontend": { "url": "...", "name": "..." },
    "backend": { "url": "...", "name": "..." },
    "storage": { "accountName": "...", "tableEndpoint": "..." },
    "identity": { "clientId": "...", "principalId": "..." },
    "monitoring": { "applicationInsightsName": "...", "connectionString": "..." }
  }
}
```

## Cost Estimation

### Development Environment
- **App Service Plan (F1)**: Free
- **Storage Account (LRS)**: ~$0.02/month
- **Static Web App (Free)**: Free
- **Application Insights**: Pay-as-you-go (minimal dev traffic)
- **Total**: ~$0-5/month

### Production Environment
- **App Service Plan (P1V3 x2)**: ~$280/month
- **Storage Account (GRS)**: ~$0.05/month
- **Static Web App (Standard)**: ~$9/month
- **Application Insights**: ~$5-20/month (based on usage)
- **Total**: ~$300/month

> **Optimization Tip**: Delete dev resources when not in use to minimize costs.

## Integration with Existing Code

The infrastructure integrates seamlessly with the existing codebase:

### Backend (`server/`)
- Expects Python 3.11+
- Reads environment variables:
  - `AZURE_STORAGE_ENDPOINT` - Auto-set by deployment
  - `AZURE_TABLE_NAME` - Auto-set to "WorkflowSessions"
  - `AZURE_CLIENT_ID` - Auto-set from managed identity
- Session store (`server/storage/session_store.py`) uses these variables

### Frontend (`client/`)
- Next.js Static Web App
- Reads build-time variables:
  - `NEXT_PUBLIC_API_URL` - Backend URL
  - `NEXT_PUBLIC_WS_URL` - WebSocket URL (wss://)
- Deployed from `client` directory in repo

## Next Steps After Deployment

1. **Configure Repository Integration**
   - Static Web App: Connect GitHub or Azure DevOps
   - Set up CI/CD workflows

2. **Deploy Application Code**
   - Backend: Deploy FastAPI app to App Service
   - Frontend: Push to connected repo (auto-deploys)

3. **Configure Custom Domains** (Production only)
   - Add DNS records
   - Enable SSL certificates

4. **Set Up Alerts**
   - Backend availability
   - Error rates
   - Performance degradation

5. **Add Azure AD Authentication** (Next major task)
   - Replace `user_id="anonymous"` with JWT tokens
   - Implement MSAL in frontend and backend

## Troubleshooting

### Role Assignment Issues
**Problem**: Backend can't access storage
**Solution**: Wait 5-10 minutes for RBAC propagation

### Storage Account Name Conflicts
**Problem**: "Name already taken"
**Solution**: Storage name uses `uniqueString()` but may conflict if deploying to same resource group. Delete old resources or use new resource group.

### Static Web App Build Failures
**Problem**: Build fails with errors
**Solution**: Check build logs in Azure Portal → Static Web App → Deployments

### Backend Not Starting
**Problem**: App Service shows "Application Error"
**Solution**: Check logs (`az webapp log tail`) for missing dependencies or Python errors

## References

- **Deployment Guide**: [README.md](./README.md)
- **Quick Start**: [QUICKSTART.md](./QUICKSTART.md)
- **Session Management**: [../docs/session-management.md](../docs/session-management.md)
- **Setup Guide**: [../docs/setup-session-storage.md](../docs/setup-session-storage.md)

## Bicep Documentation Used

This infrastructure was created based on:
- [Azure Bicep Documentation](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- Context7 library ID: `/azure/bicep`
- Modules, parameters, outputs patterns
- App Service, Storage, Static Web App best practices

---

**Infrastructure is ready for deployment!** 🚀

Follow the [QUICKSTART.md](./QUICKSTART.md) guide for a 10-minute deployment walkthrough.
