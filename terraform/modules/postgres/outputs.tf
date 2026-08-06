output "postgres_server_id" {
  value       = azurerm_postgresql_flexible_server.postgres.id
  description = "Resource ID of PostgreSQL Flexible Server"
}

output "postgres_fqdn" {
  value       = azurerm_postgresql_flexible_server.postgres.fqdn
  description = "Fully Qualified Domain Name of PostgreSQL Server"
}

output "postgres_database_name" {
  value       = azurerm_postgresql_flexible_server_database.complianceiq_db.name
  description = "Database name"
}

output "administrator_login" {
  value       = azurerm_postgresql_flexible_server.postgres.administrator_login
  description = "PostgreSQL administrator login username"
}
