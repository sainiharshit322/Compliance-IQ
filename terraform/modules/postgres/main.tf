# Terraform Module: PostgreSQL Flexible Server (B1MS Free Tier + pgvector)
# Architecture Spec: docs/specs/02_architecture.md (Section 4 & 5) & 03_database_schema.md

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_postgresql_flexible_server" "postgres" {
  name                   = "psql-complianceiq-${var.environment}-${random_string.suffix.result}"
  resource_group_name    = var.resource_group_name
  location               = var.location
  version                = "15"
  administrator_login    = var.administrator_login
  administrator_password = var.administrator_password

  sku_name   = "B_Standard_B1ms"
  storage_mb = 32768

  backup_retention_days        = 7
  geo_redundant_backup_enabled = false

  tags = var.tags
}

# Enable pgvector and uuid-ossp PostgreSQL extensions
resource "azurerm_postgresql_flexible_server_configuration" "pgvector_extension" {
  name      = "azure.extensions"
  server_id = azurerm_postgresql_flexible_server.postgres.id
  value     = "VECTOR,UUID-OSSP"
}

# ComplianceIQ Main Database
resource "azurerm_postgresql_flexible_server_database" "complianceiq_db" {
  name      = "complianceiq"
  server_id = azurerm_postgresql_flexible_server.postgres.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# Allow Azure internal services firewall rule (0.0.0.0)
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" {
  name             = "allow-azure-internal-services"
  server_id        = azurerm_postgresql_flexible_server.postgres.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}
