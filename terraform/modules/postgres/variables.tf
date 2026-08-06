variable "location" {
  type        = string
  description = "Azure Region for PostgreSQL deployment"
}

variable "resource_group_name" {
  type        = string
  description = "Resource Group Name"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
  default     = "dev"
}

variable "tags" {
  type        = map(string)
  description = "Resource tags"
  default     = {}
}

variable "administrator_login" {
  type        = string
  description = "PostgreSQL administrator login username"
  default     = "dbadmin"
}

variable "administrator_password" {
  type        = string
  description = "PostgreSQL administrator login password"
  sensitive   = true
  default     = "ComplianceIQ_2026_Secure!"
}
