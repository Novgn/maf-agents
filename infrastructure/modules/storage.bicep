// ====================================================================================================
// Azure Storage Account Module
// ====================================================================================================
// Creates an Azure Storage Account configured for:
// - Table Storage (session management)
// - Secure access via managed identity
// - Minimum TLS 1.2
// - HTTPS-only traffic
// ====================================================================================================

@description('Name of the storage account (must be globally unique, 3-24 lowercase alphanumeric characters)')
@minLength(3)
@maxLength(24)
param storageAccountName string

@description('Azure region for the storage account')
param location string

@description('Tags to apply to the resource')
param tags object = {}

@description('Storage account SKU')
param sku object = {
  name: 'Standard_LRS'
}

@description('Principal ID of the managed identity to grant access')
param managedIdentityPrincipalId string

// Azure built-in role definition IDs
var storageTableDataContributorRoleId = '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3'

// ====================================================================================================
// Resources
// ====================================================================================================

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: sku
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true // Required for Table Storage with managed identity
    encryption: {
      services: {
        blob: {
          enabled: true
        }
        file: {
          enabled: true
        }
        table: {
          enabled: true
        }
        queue: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow' // Change to 'Deny' and add specific IP rules for production
    }
  }

  // Table service (for session storage)
  resource tableService 'tableServices' = {
    name: 'default'

    // WorkflowSessions table will be created automatically by the application
    // but we can pre-create it here if desired
    resource workflowSessionsTable 'tables' = {
      name: 'WorkflowSessions'
    }
  }
}

// Role assignment to grant managed identity access to Table Storage
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, storageTableDataContributorRoleId, managedIdentityPrincipalId)
  scope: storageAccount
  properties: {
    principalId: managedIdentityPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageTableDataContributorRoleId)
    principalType: 'ServicePrincipal'
    description: 'Grant the managed identity Storage Table Data Contributor role for session management'
  }
}

// ====================================================================================================
// Outputs
// ====================================================================================================

@description('The resource ID of the storage account')
output storageAccountId string = storageAccount.id

@description('The name of the storage account')
output storageAccountName string = storageAccount.name

@description('The primary endpoint for Table Storage')
output tableEndpoint string = storageAccount.properties.primaryEndpoints.table

@description('The primary endpoint for Blob Storage')
output blobEndpoint string = storageAccount.properties.primaryEndpoints.blob

@description('The primary endpoint for Queue Storage')
output queueEndpoint string = storageAccount.properties.primaryEndpoints.queue

@description('Connection information for the application')
output connectionInfo object = {
  storageAccountName: storageAccount.name
  tableEndpoint: storageAccount.properties.primaryEndpoints.table
  tableName: 'WorkflowSessions'
}
