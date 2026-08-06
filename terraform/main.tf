# ComplianceIQ - Root Infrastructure as Code (Terraform)
# Targeting Azure $0 / Free Tier Specifications

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

module "storage" {
  source                   = "./modules/storage"
  location                 = azurerm_resource_group.rg.location
  resource_group_name      = azurerm_resource_group.rg.name
  environment              = var.environment
  retention_period_in_days = var.storage_retention_period_in_days
  tags                     = var.tags
}

module "identity" {
  source                             = "./modules/identity"
  location                           = azurerm_resource_group.rg.location
  resource_group_name                = azurerm_resource_group.rg.name
  environment                        = var.environment
  worm_container_resource_manager_id = module.storage.worm_container_resource_manager_id
  evidence_queue_id                  = module.storage.queue_id
  tags                               = var.tags
}

module "postgres" {
  source                 = "./modules/postgres"
  location               = azurerm_resource_group.rg.location
  resource_group_name    = azurerm_resource_group.rg.name
  environment            = var.environment
  administrator_login    = var.postgres_admin_username
  administrator_password = var.postgres_admin_password
  tags                   = var.tags
}

module "cosmos" {
  source              = "./modules/cosmos"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  environment         = var.environment
  enable_free_tier    = true
  tags                = var.tags
}

module "container_apps" {
  source              = "./modules/container_apps"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  environment         = var.environment
  tags                = var.tags
}
