variable "location" {
  type        = string
  description = "Azure Region for storage deployment"
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

variable "retention_period_in_days" {
  type        = number
  description = "Retention period in days for WORM Blob container immutability policy"
  default     = 30
}

variable "immutability_state" {
  type        = string
  description = "State of immutability policy (unlocked or locked)"
  default     = "unlocked"
}
