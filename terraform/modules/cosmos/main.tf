# Terraform Module: Cosmos DB Free Tier + Append-Only Audit Container
# Architecture Spec: docs/specs/02_architecture.md (Section 4, 5 & 6)

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_cosmosdb_account" "cosmos" {
  name                = "cosmos-complianceiq-${var.environment}-${random_string.suffix.result}"
  location            = var.location
  resource_group_name = var.resource_group_name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"
  enable_free_tier    = var.enable_free_tier

  consistency_policy {
    consistency_level       = "Session"
    max_interval_in_seconds = 5
    max_staleness_prefix    = 100
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }

  tags = var.tags
}

# Database for Immutable Audit Trail Log
resource "azurerm_cosmosdb_sql_database" "audit_db" {
  name                = "compliance_audit"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.cosmos.name
}

# Append-Only Audit Trail Container
resource "azurerm_cosmosdb_sql_container" "audit_trails" {
  name                = "audit_trails"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.cosmos.name
  database_name       = azurerm_cosmosdb_sql_database.audit_db.name
  partition_key_path  = "/framework_id"

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }
  }
}

# Append-Only Data Plane Role Definition (Restricting Update & Delete)
resource "azurerm_cosmosdb_sql_role_definition" "append_only_role" {
  name                = "CosmosDBAppendOnlyAuditRole"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.cosmos.name
  type                = "CustomRole"
  assignable_scopes   = [azurerm_cosmosdb_account.cosmos.id]

  permissions {
    data_actions = [
      "Microsoft.DocumentDB/databaseAccounts/readMetadata",
      "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/create",
      "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/read"
    ]
  }
}
