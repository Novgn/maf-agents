# Quick Start Guide - MAF Agents Infrastructure Deployment

This guide will get you from zero to deployed in under 10 minutes.

## Prerequisites

```bash
# 1. Verify Azure CLI is installed and you're logged in
az --version
az login
az account show

# 2. Verify Bicep is installed
az bicep version

# 3. Set your Azure subscription (if you have multiple)
az account set --subscription "Your Subscription Name"
```

## Deploy to Development

### Step 1: Create Resource Group

```bash
# Create a resource group for development
az group create \
  --name rg-maf-agents-dev \
  --location eastus

# Verify it was created
az group show --name rg-maf-agents-dev
```

### Step 2: Deploy Infrastructure

```bash
# Navigate to infrastructure directory
cd infrastructure

# Deploy (this takes 5-10 minutes)
az deployment group create \
  --resource-group rg-maf-agents-dev \
  --template-file main.bicep \
  --parameters @parameters/dev.parameters.json \
  --name maf-agents-dev-$(date +%Y%m%d-%H%M%S)
```

### Step 3: Capture Outputs

```bash
# Save deployment name for later
DEPLOYMENT_NAME="maf-agents-dev-TIMESTAMP"  # Replace with actual timestamp from previous command

# Get all outputs
az deployment group show \
  --resource-group rg-maf-agents-dev \
  --name $DEPLOYMENT_NAME \
  --query properties.outputs

# Get specific URLs
FRONTEND_URL=$(az deployment group show \
  --resource-group rg-maf-agents-dev \
  --name $DEPLOYMENT_NAME \
  --query properties.outputs.frontendUrl.value -o tsv)

BACKEND_URL=$(az deployment group show \
  --resource-group rg-maf-agents-dev \
  --name $DEPLOYMENT_NAME \
  --query properties.outputs.backendApiUrl.value -o tsv)

STORAGE_ENDPOINT=$(az deployment group show \
  --resource-group rg-maf-agents-dev \
  --name $DEPLOYMENT_NAME \
  --query properties.outputs.storageTableEndpoint.value -o tsv)

echo "Frontend: $FRONTEND_URL"
echo "Backend: $BACKEND_URL"
echo "Storage: $STORAGE_ENDPOINT"
```

### Step 4: Configure GitHub Actions (Frontend Deployment)

```bash
# Get the Static Web App deployment token
STATIC_WEB_APP_NAME=$(az deployment group show \
  --resource-group rg-maf-agents-dev \
  --name $DEPLOYMENT_NAME \
  --query "properties.outputs.deploymentSummary.value.frontend.name" -o tsv)

SWA_TOKEN=$(az staticwebapp secrets list \
  --name $STATIC_WEB_APP_NAME \
  --resource-group rg-maf-agents-dev \
  --query properties.apiKey -o tsv)

echo "Add this token as AZURE_STATIC_WEB_APPS_API_TOKEN secret in GitHub:"
echo $SWA_TOKEN
```

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret:
- Name: `AZURE_STATIC_WEB_APPS_API_TOKEN`
- Value: (paste the token from above)

### Step 5: Deploy Backend Code

```bash
# Navigate to server directory
cd ../server

# Create deployment zip
zip -r dist.zip . -x "*.git*" -x "*__pycache__*" -x "*.env*"

# Get backend app service name
BACKEND_APP_NAME=$(az deployment group show \
  --resource-group rg-maf-agents-dev \
  --name $DEPLOYMENT_NAME \
  --query "properties.outputs.deploymentSummary.value.backend.name" -o tsv)

# Deploy
az webapp deployment source config-zip \
  --resource-group rg-maf-agents-dev \
  --name $BACKEND_APP_NAME \
  --src dist.zip

# Clean up
rm dist.zip
```

### Step 6: Verify Deployment

```bash
# Test backend health endpoint
curl https://$BACKEND_URL/health

# Expected output: {"status":"healthy"}

# Open backend API docs
open https://$BACKEND_URL/docs

# Open frontend (may take a few minutes to build)
open https://$FRONTEND_URL
```

## Troubleshooting

### "Deployment failed" - Check the error

```bash
az deployment group show \
  --resource-group rg-maf-agents-dev \
  --name $DEPLOYMENT_NAME \
  --query properties.error
```

### Backend not starting - Check logs

```bash
az webapp log tail \
  --resource-group rg-maf-agents-dev \
  --name $BACKEND_APP_NAME
```

### Storage access issues - Verify role assignment

```bash
# Get managed identity principal ID
MI_PRINCIPAL_ID=$(az deployment group show \
  --resource-group rg-maf-agents-dev \
  --name $DEPLOYMENT_NAME \
  --query "properties.outputs.deploymentSummary.value.identity.principalId" -o tsv)

# Check role assignments
az role assignment list --assignee $MI_PRINCIPAL_ID
```

Wait 5-10 minutes for RBAC propagation if you see permission errors.

## Clean Up

When you're done testing:

```bash
# Delete the entire resource group (CAUTION!)
az group delete --name rg-maf-agents-dev --yes --no-wait
```

## Next Steps

1. **Set up CI/CD**:
   - Frontend: GitHub Actions (`.github/workflows/azure-static-web-apps.yml`)
   - Backend: GitHub Actions or Azure DevOps pipeline

2. **Configure Custom Domains**:
   - See [README.md](./README.md#configure-custom-domains-optional)

3. **Enable Monitoring**:
   - View Application Insights in Azure Portal
   - Set up alerts for errors and performance

4. **Deploy to Production**:
   - Use `parameters/prod.parameters.json`
   - Create separate resource group (`rg-maf-agents-prod`)
   - Configure production settings (IP restrictions, autoscaling, etc.)

## Reference

- Full documentation: [README.md](./README.md)
- Session management setup: [../docs/setup-session-storage.md](../docs/setup-session-storage.md)
- Architecture details: [../docs/session-management.md](../docs/session-management.md)
