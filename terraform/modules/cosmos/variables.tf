variable "location" {
  type        = string
  description = "Azure Region for Cosmos DB deployment"
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

variable "enable_free_tier" {
  type        = bool
  description = "Enable Cosmos DB Free Tier (1,000 RU/s and 25 GB storage free)"
  default     = true
}
