variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "ws-translation"
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs (at least 2 subnets across 2 AZs)"
  type        = list(string)
}

variable "security_group_id" {
  description = "Security Group ID of the ALB"
  type        = string
}
