output "cosmos_account_id" {
  value       = azurerm_cosmosdb_account.cosmos.id
  description = "Resource ID of Cosmos DB Account"
}

output "cosmos_endpoint" {
  value       = azurerm_cosmosdb_account.cosmos.endpoint
  description = "Document Endpoint URI of Cosmos DB Account"
}

output "primary_key" {
  value       = azurerm_cosmosdb_account.cosmos.primary_key
  description = "Primary Master Key for Cosmos DB"
  sensitive   = true
}

output "database_name" {
  value       = azurerm_cosmosdb_sql_database.audit_db.name
  description = "Audit Trail Database Name"
}

output "container_name" {
  value       = azurerm_cosmosdb_sql_container.audit_trails.name
  description = "Append-Only Audit Trails Container Name"
}

output "append_only_role_id" {
  value       = azurerm_cosmosdb_sql_role_definition.append_only_role.id
  description = "Resource ID of Data Plane Append-Only Role Definition"
}
