// ====================================================================================================
// MAF Agents Infrastructure - Main Deployment Template
// ====================================================================================================
// This template deploys all infrastructure required for the maf-agents application:
// - Azure Storage Account (Table Storage for session management)
// - Azure App Service Plan & App Service (FastAPI backend)
// - Azure Static Web App (Next.js frontend)
// - User-Assigned Managed Identity
// - Application Insights (monitoring)
// - Role assignments for least-privilege access
// ====================================================================================================

targetScope = 'resourceGroup'

// ====================================================================================================
// Parameters
// ====================================================================================================

@description('The Azure region where resources will be deployed')
param location string = resourceGroup().location

@description('Environment name (dev, staging, prod)')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environmentName string

@description('Unique suffix for globally unique resource names')
@maxLength(13)
param resourceNameSuffix string = uniqueString(resourceGroup().id)

@description('Tags to apply to all resources')
param tags object = {
  Project: 'MAF-Agents'
  Environment: environmentName
  ManagedBy: 'Bicep'
}

// Optional parameters for customization
@description('Azure DevOps organization URL for repository access')
param azureDevOpsOrgUrl string = ''

@description('Azure DevOps project name')
param azureDevOpsProject string = ''

@description('Azure DevOps repository name')
param azureDevOpsRepo string = ''

// ====================================================================================================
// Variables
// ====================================================================================================

var appName = 'maf-agents'

// Resource naming convention: {appName}-{resourceType}-{environment}-{suffix}
// Storage account names must be 3-24 characters, lowercase alphanumeric only
var storageAccountName = toLower('mafagent${take(resourceNameSuffix, 10)}')
var appServicePlanName = '${appName}-asp-${environmentName}'
var backendAppServiceName = '${appName}-api-${environmentName}-${resourceNameSuffix}'
var frontendStaticWebAppName = '${appName}-web-${environmentName}'
var managedIdentityName = '${appName}-identity-${environmentName}'
var applicationInsightsName = '${appName}-insights-${environmentName}'
var logAnalyticsWorkspaceName = '${appName}-logs-${environmentName}'

// Environment-specific SKU configurations
var environmentConfig = {
  dev: {
    appServicePlan: {
      sku: {
        name: 'F1'
        tier: 'Free'
        capacity: 1
      }
    }
    storageAccount: {
      sku: {
        name: 'Standard_LRS'
      }
    }
    staticWebApp: {
      sku: {
        name: 'Free'
        tier: 'Free'
      }
    }
  }
  staging: {
    appServicePlan: {
      sku: {
        name: 'B1'
        tier: 'Basic'
        capacity: 1
      }
    }
    storageAccount: {
      sku: {
        name: 'Standard_LRS'
      }
    }
    staticWebApp: {
      sku: {
        name: 'Standard'
        tier: 'Standard'
      }
    }
  }
  prod: {
    appServicePlan: {
      sku: {
        name: 'P1V3'
        tier: 'PremiumV3'
        capacity: 2
      }
    }
    storageAccount: {
      sku: {
        name: 'Standard_GRS'
      }
    }
    staticWebApp: {
      sku: {
        name: 'Standard'
        tier: 'Standard'
      }
    }
  }
}

// ====================================================================================================
// Module Deployments
// ====================================================================================================

// 1. User-Assigned Managed Identity
module identity 'modules/identity.bicep' = {
  name: 'identity-deployment'
  params: {
    managedIdentityName: managedIdentityName
    location: location
    tags: tags
  }
}

// 2. Log Analytics Workspace (for Application Insights)
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// 3. Application Insights
module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring-deployment'
  params: {
    applicationInsightsName: applicationInsightsName
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalyticsWorkspace.id
  }
}

// 4. Storage Account (Azure Table Storage for session management)
module storage 'modules/storage.bicep' = {
  name: 'storage-deployment'
  params: {
    storageAccountName: storageAccountName
    location: location
    tags: tags
    sku: environmentConfig[environmentName].storageAccount.sku
    managedIdentityPrincipalId: identity.outputs.principalId
  }
}

// 5. App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: environmentConfig[environmentName].appServicePlan.sku
  kind: 'linux'
  properties: {
    reserved: true // Required for Linux
  }
}

// 6. Backend App Service (FastAPI)
module backend 'modules/backend.bicep' = {
  name: 'backend-deployment'
  params: {
    appServiceName: backendAppServiceName
    location: location
    tags: tags
    appServicePlanId: appServicePlan.id
    managedIdentityId: identity.outputs.id
    managedIdentityClientId: identity.outputs.clientId
    storageTableEndpoint: storage.outputs.tableEndpoint
    applicationInsightsConnectionString: monitoring.outputs.connectionString
    applicationInsightsInstrumentationKey: monitoring.outputs.instrumentationKey
    azureDevOpsOrgUrl: azureDevOpsOrgUrl
    azureDevOpsProject: azureDevOpsProject
    azureDevOpsRepo: azureDevOpsRepo
  }
}

// 7. Frontend Static Web App (Next.js)
module frontend 'modules/frontend.bicep' = {
  name: 'frontend-deployment'
  params: {
    staticWebAppName: frontendStaticWebAppName
    location: location
    tags: tags
    sku: environmentConfig[environmentName].staticWebApp.sku
    backendApiUrl: backend.outputs.appServiceUrl
  }
}

// 8. Role Assignments - Grant managed identity access to storage
// Note: Role assignments are handled in the storage module to avoid circular dependencies

// ====================================================================================================
// Outputs
// ====================================================================================================

@description('The name of the deployed storage account')
output storageAccountName string = storage.outputs.storageAccountName

@description('The Table Storage endpoint URL')
output storageTableEndpoint string = storage.outputs.tableEndpoint

@description('The backend API URL')
output backendApiUrl string = backend.outputs.appServiceUrl

@description('The frontend URL')
output frontendUrl string = frontend.outputs.staticWebAppUrl

@description('The Application Insights connection string')
output applicationInsightsConnectionString string = monitoring.outputs.connectionString

@description('The managed identity client ID')
output managedIdentityClientId string = identity.outputs.clientId

@description('The managed identity resource ID')
output managedIdentityId string = identity.outputs.id

@description('Deployment summary with all important URLs and identifiers')
output deploymentSummary object = {
  environment: environmentName
  location: location
  frontend: {
    url: frontend.outputs.staticWebAppUrl
    name: frontendStaticWebAppName
  }
  backend: {
    url: backend.outputs.appServiceUrl
    name: backendAppServiceName
  }
  storage: {
    accountName: storage.outputs.storageAccountName
    tableEndpoint: storage.outputs.tableEndpoint
  }
  identity: {
    clientId: identity.outputs.clientId
    principalId: identity.outputs.principalId
  }
  monitoring: {
    applicationInsightsName: applicationInsightsName
    connectionString: monitoring.outputs.connectionString
  }
}
