variable "location" {
  type        = string
  description = "Azure Region for Container Apps deployment"
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

variable "collector_identity_id" {
  type        = string
  description = "User-Assigned Identity ID for Evidence Collector Agent"
  default     = ""
}

variable "gap_analysis_identity_id" {
  type        = string
  description = "User-Assigned Identity ID for Gap Analysis Agent"
  default     = ""
}

variable "api_identity_id" {
  type        = string
  description = "User-Assigned Identity ID for API Gateway"
  default     = ""
}
