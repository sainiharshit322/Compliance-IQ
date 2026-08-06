output "collector_identity_id" {
  value       = azurerm_user_assigned_identity.collector.id
  description = "Resource ID of Evidence Collector Managed Identity"
}

output "collector_principal_id" {
  value       = azurerm_user_assigned_identity.collector.principal_id
  description = "Principal ID of Evidence Collector Managed Identity"
}

output "collector_client_id" {
  value       = azurerm_user_assigned_identity.collector.client_id
  description = "Client ID of Evidence Collector Managed Identity"
}

output "gap_analysis_identity_id" {
  value       = azurerm_user_assigned_identity.gap_analysis.id
  description = "Resource ID of Gap Analysis Agent Managed Identity"
}

output "gap_analysis_principal_id" {
  value       = azurerm_user_assigned_identity.gap_analysis.principal_id
  description = "Principal ID of Gap Analysis Agent Managed Identity"
}

output "gap_analysis_client_id" {
  value       = azurerm_user_assigned_identity.gap_analysis.client_id
  description = "Client ID of Gap Analysis Agent Managed Identity"
}

output "api_identity_id" {
  value       = azurerm_user_assigned_identity.api.id
  description = "Resource ID of API Gateway Managed Identity"
}

output "api_principal_id" {
  value       = azurerm_user_assigned_identity.api.principal_id
  description = "Principal ID of API Gateway Managed Identity"
}

output "api_client_id" {
  value       = azurerm_user_assigned_identity.api.client_id
  description = "Client ID of API Gateway Managed Identity"
}
