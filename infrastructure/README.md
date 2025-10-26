# MAF Agents Infrastructure

Infrastructure as Code (IaC) for deploying the MAF Agents application to Azure using Bicep templates.

## Architecture Overview

The infrastructure deploys a complete, production-ready environment including:

### Core Components

1. **Frontend** - Azure Static Web App (Next.js)
   - Global CDN distribution
   - Automatic HTTPS
   - CI/CD integration (GitHub Actions or Azure DevOps)

2. **Backend** - Azure App Service (FastAPI)
   - Python 3.11 runtime
   - WebSocket support for real-time agent communication
   - Managed identity authentication
   - Auto-scaling support

3. **Storage** - Azure Storage Account (Table Storage)
   - Session management
   - Conversation history persistence
   - Workflow state tracking

4. **Identity** - User-Assigned Managed Identity
   - Passwordless authentication
   - Least-privilege access to Azure resources
   - Azure DevOps integration

5. **Monitoring** - Application Insights + Log Analytics
   - Performance monitoring
   - Error tracking
   - Custom metrics and dashboards

### Security Features

- ✅ **No secrets in code** - Managed identity for all Azure service authentication
- ✅ **HTTPS-only** - All traffic encrypted in transit
- ✅ **TLS 1.2+** - Minimum TLS version enforced
- ✅ **Role-Based Access Control (RBAC)** - Least-privilege role assignments
- ✅ **Network security** - Configurable IP restrictions
- ✅ **Encryption at rest** - Azure-managed encryption for all storage

## Prerequisites

Before deploying, ensure you have:

1. **Azure CLI** installed and logged in:

   ```bash
   az --version
   az login
   az account show
   ```

2. **Bicep CLI** (usually installed with Azure CLI):

   ```bash
   az bicep version
   # If not installed:
   az bicep install
   ```

3. **Azure Subscription** with appropriate permissions:
   - Contributor or Owner role on the subscription or resource group
   - User Access Administrator role (for role assignments)

4. **Resource Group** (or create one):

   ```bash
   az group create --name rg-maf-agents-dev --location eastus
   ```

## Deployment

### Quick Start - Development Environment

Deploy the entire stack to a development environment:

```bash
# 1. Navigate to the infrastructure directory
cd infrastructure

# 2. Validate the Bicep template
az deployment group validate \
  --resource-group rg-maf-agents-dev \
  --template-file main.bicep \
  --parameters @parameters/dev.bicepparam

# 3. Preview changes (What-If)
az deployment group what-if \
  --resource-group rg-maf-agents-dev \
  --template-file main.bicep \
  --parameters @parameters/dev.bicepparam

# 4. Deploy
az deployment group create \
  --resource-group rg-maf-agents-dev \
  --template-file main.bicep \
  --parameters @parameters/dev.bicepparam \
  --name maf-agents-deployment-$(date +%Y%m%d-%H%M%S)
```

### Production Deployment

For production, use the prod parameter file:

```bash
az deployment group create \
  --resource-group rg-maf-agents-prod \
  --template-file main.bicep \
  --parameters @parameters/prod.bicepparam \
  --name maf-agents-prod-$(date +%Y%m%d-%H%M%S)
```

### Deployment Outputs

After deployment completes, capture the outputs:

```bash
# Get all outputs as JSON
az deployment group show \
  --resource-group rg-maf-agents-dev \
  --name maf-agents-deployment-TIMESTAMP \
  --query properties.outputs

# Get specific outputs
az deployment group show \
  --resource-group rg-maf-agents-dev \
  --name maf-agents-deployment-TIMESTAMP \
  --query properties.outputs.frontendUrl.value -o tsv

az deployment group show \
  --resource-group rg-maf-agents-dev \
  --name maf-agents-deployment-TIMESTAMP \
  --query properties.outputs.backendApiUrl.value -o tsv
```

Key outputs include:

- `frontendUrl` - Your Static Web App URL
- `backendApiUrl` - Your FastAPI backend URL
- `storageAccountName` - Azure Storage account name
- `managedIdentityClientId` - Managed identity client ID
- `applicationInsightsConnectionString` - App Insights connection string

## Post-Deployment Configuration

### 1. Configure Static Web App Deployment

The Static Web App requires GitHub or Azure DevOps integration for CI/CD:

#### Option A: GitHub Actions

1. Get the deployment token:

   ```bash
   az staticwebapp secrets list \
     --name <static-web-app-name> \
     --resource-group rg-maf-agents-dev \
     --query properties.apiKey -o tsv
   ```

2. Add it as a GitHub secret named `AZURE_STATIC_WEB_APPS_API_TOKEN`

3. Add the GitHub Actions workflow (see `.github/workflows/static-web-app.yml`)

#### Option B: Azure DevOps

1. In Azure Portal, go to your Static Web App
2. Click "Deployment" → "Azure DevOps"
3. Follow the wizard to connect your Azure Repo

### 2. Configure Backend Deployment

Deploy your FastAPI application to the App Service:

```bash
# From the server directory
cd ../server

# Deploy via zip
az webapp deployment source config-zip \
  --resource-group rg-maf-agents-dev \
  --name <backend-app-service-name> \
  --src dist.zip

# Or use local Git deployment
az webapp deployment user set --user-name <username> --password <password>
git remote add azure <git-url>
git push azure main:master
```

### 3. Verify Deployment

Test the deployed services:

```bash
# Test backend health endpoint
curl https://<backend-url>/health

# Test backend API docs
open https://<backend-url>/docs

# Test frontend
open https://<frontend-url>
```

### 4. Configure Custom Domains (Optional)

For production, configure custom domains:

```bash
# Add custom domain to Static Web App (requires Standard SKU)
az staticwebapp hostname set \
  --name <static-web-app-name> \
  --resource-group rg-maf-agents-prod \
  --hostname www.yourdomain.com

# Add custom domain to App Service
az webapp config hostname add \
  --resource-group rg-maf-agents-prod \
  --webapp-name <backend-app-service-name> \
  --hostname api.yourdomain.com
```

## Environment-Specific SKUs

The infrastructure automatically provisions different SKUs based on environment:

### Development (`dev`)

- **App Service Plan**: F1 (Free)
- **Storage Account**: Standard_LRS (Locally Redundant)
- **Static Web App**: Free
- **Estimated Cost**: ~$0-5/month

### Staging (`staging`)

- **App Service Plan**: B1 (Basic)
- **Storage Account**: Standard_LRS
- **Static Web App**: Standard
- **Estimated Cost**: ~$55/month

### Production (`prod`)

- **App Service Plan**: P1V3 (Premium V3) with 2 instances
- **Storage Account**: Standard_GRS (Geo-Redundant)
- **Static Web App**: Standard
- **Estimated Cost**: ~$300/month

> **Note**: Costs are estimates and may vary based on usage.

## Customization

### Modify Resource SKUs

Edit the `environmentConfig` variable in `main.bicep`:

```bicep
var environmentConfig = {
  dev: {
    appServicePlan: {
      sku: {
        name: 'F1'  // Change to B1, S1, P1V3, etc.
        tier: 'Free'
        capacity: 1
      }
    }
    // ... other configurations
  }
}
```

### Add Azure DevOps Integration

Update the parameter files (`parameters/dev.bicepparam`):

```bicep
param azureDevOpsOrgUrl = 'https://dev.azure.com/your-org'
param azureDevOpsProject = 'YourProject'
param azureDevOpsRepo = 'maf-agents'
```

### Enable IP Restrictions

For production security, restrict access by IP:

Edit `modules/backend.bicep` in the `ipSecurityRestrictions` section:

```bicep
ipSecurityRestrictions: [
  {
    ipAddress: '203.0.113.0/24'  // Your office IP range
    action: 'Allow'
    priority: 100
    name: 'Allow Office'
  }
  {
    ipAddress: 'Any'
    action: 'Deny'
    priority: 2147483647
    name: 'Deny all others'
  }
]
```

## Troubleshooting

### Deployment Fails with "Name already taken"

Resource names must be globally unique. The template uses `uniqueString(resourceGroup().id)` to generate unique suffixes, but if deploying to the same resource group multiple times, names may conflict.

**Solution**: Delete the old resources or use a different resource group.

### Managed Identity Permission Errors

If the backend can't access storage:

1. Verify role assignment:

   ```bash
   az role assignment list \
     --assignee <managed-identity-principal-id> \
     --scope <storage-account-id>
   ```

2. It may take a few minutes for RBAC changes to propagate. Wait 5-10 minutes and retry.

### Static Web App Deployment Token Not Working

Regenerate the token:

```bash
az staticwebapp secrets reset-api-key \
  --name <static-web-app-name> \
  --resource-group rg-maf-agents-dev
```

### Backend App Service Not Starting

Check logs:

```bash
# Stream live logs
az webapp log tail \
  --resource-group rg-maf-agents-dev \
  --name <backend-app-service-name>

# Download logs
az webapp log download \
  --resource-group rg-maf-agents-dev \
  --name <backend-app-service-name> \
  --log-file logs.zip
```

Common issues:

- Missing dependencies in `requirements.txt`
- Incorrect Python version
- Missing environment variables

## Cleanup

To delete all resources:

```bash
# Delete the entire resource group (CAUTION: This deletes everything!)
az group delete --name rg-maf-agents-dev --yes --no-wait

# Or delete specific deployment
az deployment group delete \
  --resource-group rg-maf-agents-dev \
  --name maf-agents-deployment-TIMESTAMP
```

## Cost Optimization

### Development

- Use Free tier SKUs where possible (F1 App Service Plan, Free Static Web App)
- Delete resources when not in use
- Use `az group delete` at end of day

### Production

- Enable autoscaling on App Service Plan
- Use Azure Reserved Instances for 1-3 year commitment (up to 72% savings)
- Set up budget alerts:

  ```bash
  az consumption budget create \
    --budget-name maf-agents-monthly-budget \
    --amount 500 \
    --time-grain Monthly \
    --resource-group rg-maf-agents-prod
  ```

## Monitoring and Alerts

### View Application Insights

```bash
# Open Application Insights in Azure Portal
az monitor app-insights component show \
  --app <application-insights-name> \
  --resource-group rg-maf-agents-dev
```

### Create Alerts

Create an alert for backend failures:

```bash
az monitor metrics alert create \
  --name backend-http-errors \
  --resource-group rg-maf-agents-prod \
  --scopes <backend-app-service-id> \
  --condition "count Http5xx > 10" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action <action-group-id>
```

## CI/CD Integration

### GitHub Actions Example

See `.github/workflows/infrastructure.yml` for automated deployments:

```yaml
name: Deploy Infrastructure

on:
  push:
    branches: [main]
    paths: ['infrastructure/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Deploy Bicep
        run: |
          az deployment group create \
            --resource-group rg-maf-agents-prod \
            --template-file infrastructure/main.bicep \
            --parameters @infrastructure/parameters/prod.bicepparam
```

## References

- [Azure Bicep Documentation](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Azure Static Web Apps](https://learn.microsoft.com/en-us/azure/static-web-apps/)
- [Azure App Service](https://learn.microsoft.com/en-us/azure/app-service/)
- [Azure Storage Table Storage](https://learn.microsoft.com/en-us/azure/storage/tables/)
- [Azure Managed Identity](https://learn.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/)

## Support

For issues or questions:

- Check the [troubleshooting section](#troubleshooting) above
- Review Azure activity logs in the Portal
- Contact the platform team
