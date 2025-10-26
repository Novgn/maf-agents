// ====================================================================================================
// Next.js Frontend Static Web App Module
// ====================================================================================================
// Creates an Azure Static Web App for the Next.js frontend with:
// - Global CDN distribution
// - Automatic HTTPS
// - Built-in CI/CD with GitHub Actions (or Azure DevOps)
// - Custom domain support
// - API integration with backend
// ====================================================================================================

@description('Name of the Static Web App')
param staticWebAppName string

@description('Azure region for the Static Web App (note: some features are region-specific)')
param location string

@description('Tags to apply to the resource')
param tags object = {}

@description('SKU configuration for the Static Web App')
param sku object = {
  name: 'Free'
  tier: 'Free'
}

@description('Backend API URL for CORS and proxying')
param backendApiUrl string

// ====================================================================================================
// Resources
// ====================================================================================================

resource staticWebApp 'Microsoft.Web/staticSites@2023-01-01' = {
  name: staticWebAppName
  location: location
  tags: tags
  sku: sku
  properties: {
    // Repository configuration (can be set post-deployment via GitHub/Azure DevOps integration)
    repositoryUrl: '' // Set this during deployment or via portal
    branch: 'main'
    buildProperties: {
      appLocation: 'client' // Next.js app location in repo
      apiLocation: '' // No built-in API functions
      outputLocation: '' // Next.js handles its own output
      appBuildCommand: 'npm run build'
      appArtifactLocation: ''
    }

    // Staging environments configuration
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true

    // Enterprise-grade edge configuration (requires Standard SKU)
    enterpriseGradeCdnStatus: sku.name == 'Standard' ? 'Enabled' : 'Disabled'
  }
}

// Configure app settings for the Static Web App
resource staticWebAppSettings 'Microsoft.Web/staticSites/config@2023-01-01' = {
  parent: staticWebApp
  name: 'appsettings'
  properties: {
    // Backend API URL for the frontend to connect to
    NEXT_PUBLIC_API_URL: backendApiUrl
    NEXT_PUBLIC_WS_URL: replace(backendApiUrl, 'https://', 'wss://')
  }
}

// Custom domain configuration (requires Standard SKU and manual DNS setup)
// Uncomment and configure after deployment:
// resource customDomain 'Microsoft.Web/staticSites/customDomains@2023-01-01' = if (sku.name == 'Standard') {
//   parent: staticWebApp
//   name: 'www.yourdomain.com'
//   properties: {}
// }

// ====================================================================================================
// Outputs
// ====================================================================================================

@description('The resource ID of the Static Web App')
output id string = staticWebApp.id

@description('The name of the Static Web App')
output name string = staticWebApp.name

@description('The default hostname of the Static Web App')
output staticWebAppUrl string = 'https://${staticWebApp.properties.defaultHostname}'

@description('The default hostname')
output defaultHostname string = staticWebApp.properties.defaultHostname

@description('The API key for deployment (sensitive - use with caution)')
#disable-next-line outputs-should-not-contain-secrets
output deploymentToken string = staticWebApp.listSecrets().properties.apiKey

@description('Deployment information')
output deploymentInfo object = {
  staticWebAppName: staticWebApp.name
  url: 'https://${staticWebApp.properties.defaultHostname}'
  repositoryUrl: staticWebApp.properties.repositoryUrl
  branch: staticWebApp.properties.branch
  sku: sku.name
}
