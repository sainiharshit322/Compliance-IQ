output "storage_account_id" {
  value       = azurerm_storage_account.storage.id
  description = "Resource ID of the Storage Account"
}

output "storage_account_name" {
  value       = azurerm_storage_account.storage.name
  description = "Globally unique Storage Account Name"
}

output "primary_access_key" {
  value       = azurerm_storage_account.storage.primary_access_key
  description = "Primary Storage Account Access Key"
  sensitive   = true
}

output "primary_connection_string" {
  value       = azurerm_storage_account.storage.primary_connection_string
  description = "Primary Storage Account Connection String"
  sensitive   = true
}

output "worm_container_name" {
  value       = azurerm_storage_container.evidence_worm.name
  description = "Name of the immutable WORM evidence container"
}

output "worm_container_resource_manager_id" {
  value       = azurerm_storage_container.evidence_worm.resource_manager_id
  description = "Resource Manager ID of WORM container"
}

output "queue_name" {
  value       = azurerm_storage_queue.evidence_jobs.name
  description = "Name of the evidence scan job queue"
}

output "queue_id" {
  value       = azurerm_storage_queue.evidence_jobs.resource_manager_id
  description = "Resource Manager ID of the evidence scan job queue"
}
