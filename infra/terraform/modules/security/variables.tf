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
  description = "VPC ID where security groups will be created"
  type        = string
}
