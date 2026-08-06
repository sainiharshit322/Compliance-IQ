variable "location" {
  type        = string
  description = "Azure Region for deployment"
  default     = "eastus"
}

variable "resource_group_name" {
  type        = string
  description = "Resource Group Name for ComplianceIQ infrastructure"
  default     = "rg-complianceiq-dev"
}

variable "environment" {
  type        = string
  description = "Target deployment environment (dev, staging, prod)"
  default     = "dev"
}

variable "tags" {
  type        = map(string)
  description = "Resource tagging taxonomy"
  default = {
    Project     = "ComplianceIQ"
    ManagedBy   = "Terraform"
    Environment = "Dev"
  }
}

variable "storage_retention_period_in_days" {
  type        = number
  description = "WORM storage container retention period in days"
  default     = 30
}

variable "postgres_admin_username" {
  type        = string
  description = "PostgreSQL Administrator Username"
  default     = "dbadmin"
}

variable "postgres_admin_password" {
  type        = string
  description = "PostgreSQL Administrator Password"
  sensitive   = true
  default     = "ComplianceIQ_2026_Secure!"
}
