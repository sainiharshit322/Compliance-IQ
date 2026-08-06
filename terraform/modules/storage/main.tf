# Terraform Module: Azure Storage Account, Queues, & WORM Blob Container
# Architecture Spec: docs/specs/02_architecture.md (Section 4 & 5)

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_storage_account" "storage" {
  name                     = "stciq${var.environment}${random_string.suffix.result}"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  access_tier              = "Hot"

  min_tls_version           = "TLS1_2"
  enable_https_traffic_only = true

  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = 7
    }

    container_delete_retention_policy {
      days = 7
    }
  }

  tags = var.tags
}

# Immutable WORM Evidence Container
resource "azurerm_storage_container" "evidence_worm" {
  name                  = "evidence-worm"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"

  metadata = {
    policy_type = "worm_legal_hold"
    retention   = "immutable"
  }
}

# WORM Management Retention & Immutability Policy
resource "azurerm_storage_management_policy" "worm_retention_policy" {
  storage_account_id = azurerm_storage_account.storage.id

  rule {
    name    = "WORMRetentionRule"
    enabled = true
    filters {
      prefix_match = ["evidence-worm/"]
      blob_types   = ["blockBlob"]
    }
    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = var.retention_period_in_days
      }
    }
  }
}

# Asynchronous Evidence Job Dispatch Queue
resource "azurerm_storage_queue" "evidence_jobs" {
  name                 = "evidence-jobs"
  storage_account_name = azurerm_storage_account.storage.name
}
