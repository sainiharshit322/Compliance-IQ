# Terraform Module: Azure User-Assigned Managed Identities & Zero-Trust RBAC Matrix
# Architecture Spec: docs/specs/02_architecture.md (Section 6)

# 1. Evidence Collector Agent Identity
resource "azurerm_user_assigned_identity" "collector" {
  name                = "id-collector-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

# 2. Gap Analysis Agent Identity
resource "azurerm_user_assigned_identity" "gap_analysis" {
  name                = "id-gap-analysis-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

# 3. API Gateway / HITL Portal Identity
resource "azurerm_user_assigned_identity" "api" {
  name                = "id-api-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

# RBAC Role Assignment: Evidence Collector -> WORM Storage Blob Data Contributor
resource "azurerm_role_assignment" "collector_blob_contributor" {
  scope                = var.worm_container_resource_manager_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.collector.principal_id
}

# RBAC Role Assignment: Evidence Collector -> Storage Queue Data Message Processor
resource "azurerm_role_assignment" "collector_queue_processor" {
  scope                = var.evidence_queue_id
  role_definition_name = "Storage Queue Data Message Processor"
  principal_id         = azurerm_user_assigned_identity.collector.principal_id
}

# RBAC Role Assignment: Gap Analysis Agent -> WORM Storage Blob Data Reader
resource "azurerm_role_assignment" "gap_analysis_blob_reader" {
  scope                = var.worm_container_resource_manager_id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_user_assigned_identity.gap_analysis.principal_id
}
