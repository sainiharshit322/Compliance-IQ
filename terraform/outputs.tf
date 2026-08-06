output "resource_group_name" {
  value       = azurerm_resource_group.rg.name
  description = "Resource Group Name"
}

output "storage_account_name" {
  value       = module.storage.storage_account_name
  description = "Azure Storage Account Name"
}

output "worm_container_name" {
  value       = module.storage.worm_container_name
  description = "Immutable WORM Storage Container Name"
}

output "evidence_queue_name" {
  value       = module.storage.queue_name
  description = "Evidence Scan Queue Name"
}

output "collector_identity_id" {
  value       = module.identity.collector_identity_id
  description = "Evidence Collector Managed Identity ID"
}

output "gap_analysis_identity_id" {
  value       = module.identity.gap_analysis_identity_id
  description = "Gap Analysis Agent Managed Identity ID"
}

output "api_identity_id" {
  value       = module.identity.api_identity_id
  description = "API Gateway Managed Identity ID"
}

output "postgres_fqdn" {
  value       = module.postgres.postgres_fqdn
  description = "PostgreSQL Flexible Server FQDN"
}

output "postgres_database_name" {
  value       = module.postgres.postgres_database_name
  description = "PostgreSQL Database Name"
}

output "cosmos_endpoint" {
  value       = module.cosmos.cosmos_endpoint
  description = "Cosmos DB Document Endpoint"
}

output "cosmos_database_name" {
  value       = module.cosmos.database_name
  description = "Cosmos DB Audit Database Name"
}

output "cosmos_container_name" {
  value       = module.cosmos.container_name
  description = "Cosmos DB Append-Only Audit Container Name"
}
