// ====================================================================================================
// User-Assigned Managed Identity Module
// ====================================================================================================
// Creates a user-assigned managed identity for the App Service to:
// - Access Azure Table Storage without connection strings
// - Access Azure Key Vault secrets
// - Access Azure DevOps repositories
// - Authenticate with other Azure services
// ====================================================================================================

@description('Name of the managed identity')
param managedIdentityName string

@description('Azure region for the managed identity')
param location string

@description('Tags to apply to the resource')
param tags object = {}

// ====================================================================================================
// Resources
// ====================================================================================================

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: managedIdentityName
  location: location
  tags: tags
}

// ====================================================================================================
// Outputs
// ====================================================================================================

@description('The resource ID of the managed identity')
output id string = managedIdentity.id

@description('The principal ID (object ID) of the managed identity')
output principalId string = managedIdentity.properties.principalId

@description('The client ID (application ID) of the managed identity')
output clientId string = managedIdentity.properties.clientId

@description('The name of the managed identity')
output name string = managedIdentity.name
