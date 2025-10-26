// ====================================================================================================
// Development Environment Parameters
// ====================================================================================================
// Use this parameter file for local development and testing.
// Deploy with: az deployment group create --parameters @parameters/dev.bicepparam
// ====================================================================================================

using '../main.bicep'

// Environment configuration
param environmentName = 'dev'
param location = 'eastus'

// Azure DevOps configuration (optional - fill in if using Azure Repos)
param azureDevOpsOrgUrl = '' // e.g., 'https://dev.azure.com/your-org'
param azureDevOpsProject = '' // e.g., 'YourProject'
param azureDevOpsRepo = '' // e.g., 'maf-agents'

// Tags for resource organization
param tags = {
  Project: 'MAF-Agents'
  Environment: 'Development'
  ManagedBy: 'Bicep'
  CostCenter: 'Engineering'
  Owner: 'DevTeam'
}

// Note: resourceNameSuffix will be auto-generated to ensure unique resource names
