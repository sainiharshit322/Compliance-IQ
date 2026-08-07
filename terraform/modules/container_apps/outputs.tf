output "container_apps_environment_id" {
  value       = azurerm_container_app_environment.cae.id
  description = "Resource ID of Container Apps Environment"
}

output "orchestrator_api_fqdn" {
  value       = azurerm_container_app.orchestrator_api.ingress[0].fqdn
  description = "FQDN endpoint for Orchestrator API Gateway"
}

output "hitl_portal_fqdn" {
  value       = azurerm_container_app.hitl_portal.ingress[0].fqdn
  description = "FQDN endpoint for HITL Portal"
}
