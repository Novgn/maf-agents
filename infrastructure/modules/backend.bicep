// ====================================================================================================
// FastAPI Backend App Service Module
// ====================================================================================================
// Creates an Azure App Service for the FastAPI backend with:
// - Python 3.10+ runtime
// - Managed identity authentication
// - Environment variables for Azure services
// - CORS configuration for frontend
// - Application Insights integration
// ====================================================================================================

@description('Name of the App Service')
param appServiceName string

@description('Azure region for the App Service')
param location string

@description('Tags to apply to the resource')
param tags object = {}

@description('Resource ID of the App Service Plan')
param appServicePlanId string

@description('Resource ID of the user-assigned managed identity')
param managedIdentityId string

@description('Client ID of the user-assigned managed identity')
param managedIdentityClientId string

@description('Table Storage endpoint URL')
param storageTableEndpoint string

@description('Application Insights connection string')
param applicationInsightsConnectionString string

@description('Application Insights instrumentation key')
param applicationInsightsInstrumentationKey string

@description('Azure DevOps organization URL')
param azureDevOpsOrgUrl string = ''

@description('Azure DevOps project name')
param azureDevOpsProject string = ''

@description('Azure DevOps repository name')
param azureDevOpsRepo string = ''

// ====================================================================================================
// Resources
// ====================================================================================================

resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: appServiceName
  location: location
  tags: tags
  kind: 'app,linux'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityId}': {}
    }
  }
  properties: {
    serverFarmId: appServicePlanId
    httpsOnly: true
    clientAffinityEnabled: false
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true

      // Application settings (environment variables)
      appSettings: [
        // Azure Storage (Table Storage for sessions)
        {
          name: 'AZURE_STORAGE_ENDPOINT'
          value: storageTableEndpoint
        }
        {
          name: 'AZURE_TABLE_NAME'
          value: 'WorkflowSessions'
        }
        {
          name: 'AZURE_CLIENT_ID'
          value: managedIdentityClientId
        }

        // Application Insights
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: applicationInsightsConnectionString
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: applicationInsightsInstrumentationKey
        }
        {
          name: 'ApplicationInsightsAgent_EXTENSION_VERSION'
          value: '~3'
        }

        // Azure DevOps (if configured)
        {
          name: 'AZURE_DEVOPS_ORG'
          value: azureDevOpsOrgUrl
        }
        {
          name: 'AZURE_DEVOPS_PROJECT'
          value: azureDevOpsProject
        }
        {
          name: 'AZURE_DEVOPS_REPO'
          value: azureDevOpsRepo
        }

        // Python / FastAPI configuration
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
        {
          name: 'POST_BUILD_COMMAND'
          value: 'echo "Build complete"'
        }

        // Logging
        {
          name: 'LOG_LEVEL'
          value: 'INFO'
        }
      ]

      // CORS configuration - allow frontend and localhost for development
      cors: {
        allowedOrigins: [
          'https://*.azurestaticapps.net' // Frontend Static Web App
          'http://localhost:3000' // Local development
          'http://localhost:3001' // Local development alternative port
        ]
        supportCredentials: true
      }

      // Health check
      healthCheckPath: '/health'
    }
  }
}

// Configure deployment settings
resource appServiceConfig 'Microsoft.Web/sites/config@2023-01-01' = {
  parent: appService
  name: 'web'
  properties: {
    numberOfWorkers: 1
    defaultDocuments: []
    netFrameworkVersion: 'v4.0'
    phpVersion: ''
    pythonVersion: ''
    nodeVersion: ''
    linuxFxVersion: 'PYTHON|3.11'
    requestTracingEnabled: false
    remoteDebuggingEnabled: false
    httpLoggingEnabled: true
    logsDirectorySizeLimit: 35
    detailedErrorLoggingEnabled: true
    publishingUsername: '$${appServiceName}'
    scmType: 'None'
    use32BitWorkerProcess: false
    webSocketsEnabled: true // Required for WebSocket support
    managedPipelineMode: 'Integrated'
    loadBalancing: 'LeastRequests'
    experiments: {
      rampUpRules: []
    }
    autoHealEnabled: false
    ipSecurityRestrictions: [
      {
        ipAddress: 'Any'
        action: 'Allow'
        priority: 2147483647
        name: 'Allow all'
        description: 'Allow all access'
      }
    ]
    scmIpSecurityRestrictions: [
      {
        ipAddress: 'Any'
        action: 'Allow'
        priority: 2147483647
        name: 'Allow all'
        description: 'Allow all access'
      }
    ]
    scmIpSecurityRestrictionsUseMain: false
    http20Enabled: true
    minTlsVersion: '1.2'
    ftpsState: 'Disabled'
  }
}

// ====================================================================================================
// Outputs
// ====================================================================================================

@description('The resource ID of the App Service')
output id string = appService.id

@description('The name of the App Service')
output name string = appService.name

@description('The default hostname of the App Service')
output appServiceUrl string = 'https://${appService.properties.defaultHostName}'

@description('The default hostname')
output defaultHostName string = appService.properties.defaultHostName

@description('The outbound IP addresses of the App Service')
output outboundIpAddresses string = appService.properties.outboundIpAddresses

@description('Deployment information')
output deploymentInfo object = {
  appServiceName: appService.name
  url: 'https://${appService.properties.defaultHostName}'
  healthCheckUrl: 'https://${appService.properties.defaultHostName}/health'
  apiDocsUrl: 'https://${appService.properties.defaultHostName}/docs'
  managedIdentityClientId: managedIdentityClientId
}
