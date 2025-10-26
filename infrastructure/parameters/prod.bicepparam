// ====================================================================================================
// Production Environment Parameters
// ====================================================================================================
// Use this parameter file for production deployments.
// Deploy with: az deployment group create --parameters @parameters/prod.bicepparam
// ====================================================================================================

using '../main.bicep'

// Environment configuration
param environmentName = 'prod'
param location = 'eastus' // Consider using a different region for production

// Azure DevOps configuration (fill in your production values)
param azureDevOpsOrgUrl = '' // e.g., 'https://dev.azure.com/your-org'
param azureDevOpsProject = '' // e.g., 'YourProject'
param azureDevOpsRepo = '' // e.g., 'maf-agents'

// Tags for resource organization
param tags = {
  Project: 'MAF-Agents'
  Environment: 'Production'
  ManagedBy: 'Bicep'
  CostCenter: 'Production'
  Owner: 'PlatformTeam'
  Criticality: 'High'
  DataClassification: 'Confidential'
}

// Note: resourceNameSuffix will be auto-generated to ensure unique resource names
