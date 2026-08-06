variable "location" {
  type        = string
  description = "Azure Region for Managed Identity deployment"
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

variable "worm_container_resource_manager_id" {
  type        = string
  description = "Resource Manager ID of the immutable WORM Blob storage container for RBAC binding"
  default     = ""
}

variable "evidence_queue_id" {
  type        = string
  description = "Resource ID of the evidence storage queue for RBAC binding"
  default     = ""
}
