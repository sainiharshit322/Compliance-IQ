# Terraform Module: Azure Container Apps Environment & Microservices Architecture
# Architecture Spec: docs/specs/02_architecture.md (Section 1, 2 & 4)

resource "azurerm_container_app_environment" "cae" {
  name                = "cae-complianceiq-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

# 1. Evidence Collector Agent Container App
resource "azurerm_container_app" "collector_agent" {
  name                         = "ca-collector-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.cae.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  identity {
    type         = var.collector_identity_id != "" ? "UserAssigned" : "None"
    identity_ids = var.collector_identity_id != "" ? [var.collector_identity_id] : null
  }

  ingress {
    external_enabled = true
    target_port      = 80
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = 1
    max_replicas = 2

    container {
      name   = "collector-agent"
      image  = "mcr.microsoft.com/azuredocs/aci-helloworld:latest"
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }

  tags = var.tags
}

# 2. Gap Analysis Agent Container App
resource "azurerm_container_app" "gap_analysis_agent" {
  name                         = "ca-gap-analysis-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.cae.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  identity {
    type         = var.gap_analysis_identity_id != "" ? "UserAssigned" : "None"
    identity_ids = var.gap_analysis_identity_id != "" ? [var.gap_analysis_identity_id] : null
  }

  ingress {
    external_enabled = true
    target_port      = 80
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = 1
    max_replicas = 2

    container {
      name   = "gap-analysis-agent"
      image  = "mcr.microsoft.com/azuredocs/aci-helloworld:latest"
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }

  tags = var.tags
}

# 3. FastAPI Orchestrator API Gateway Container App
resource "azurerm_container_app" "orchestrator_api" {
  name                         = "ca-orchestrator-api-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.cae.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  identity {
    type         = var.api_identity_id != "" ? "UserAssigned" : "None"
    identity_ids = var.api_identity_id != "" ? [var.api_identity_id] : null
  }

  ingress {
    external_enabled = true
    target_port      = 80
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = 1
    max_replicas = 2

    container {
      name   = "orchestrator-api"
      image  = "mcr.microsoft.com/azuredocs/aci-helloworld:latest"
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }

  tags = var.tags
}

# 4. Next.js 14 HITL Portal Container App
resource "azurerm_container_app" "hitl_portal" {
  name                         = "ca-hitl-portal-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.cae.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  ingress {
    external_enabled = true
    target_port      = 80
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = 1
    max_replicas = 2

    container {
      name   = "hitl-portal"
      image  = "mcr.microsoft.com/azuredocs/aci-helloworld:latest"
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }

  tags = var.tags
}
