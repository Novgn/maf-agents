// ====================================================================================================
// Application Insights Module
// ====================================================================================================
// Creates Application Insights for monitoring:
// - API performance and availability
// - Frontend user interactions
// - Agent execution telemetry
// - Custom metrics and logs
// ====================================================================================================

@description('Name of the Application Insights instance')
param applicationInsightsName string

@description('Azure region for Application Insights')
param location string

@description('Tags to apply to the resource')
param tags object = {}

@description('Resource ID of the Log Analytics workspace')
param logAnalyticsWorkspaceId string

// ====================================================================================================
// Resources
// ====================================================================================================

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: applicationInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspaceId
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    RetentionInDays: 30
  }
}

// ====================================================================================================
// Outputs
// ====================================================================================================

@description('The resource ID of Application Insights')
output id string = applicationInsights.id

@description('The name of Application Insights')
output name string = applicationInsights.name

@description('The instrumentation key for Application Insights')
output instrumentationKey string = applicationInsights.properties.InstrumentationKey

@description('The connection string for Application Insights')
output connectionString string = applicationInsights.properties.ConnectionString

@description('The Application ID')
output appId string = applicationInsights.properties.AppId
