variable "environment" {
  description = "Deployment environment name (e.g. dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Project identifier used in resource names"
  type        = string
  default     = "ws-translation"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "primary_az" {
  description = "Primary Availability Zone for compute and in-memory cache"
  type        = string
  default     = "ap-southeast-1a"
}

variable "secondary_az" {
  description = "Secondary Availability Zone for multi-AZ compliance (ALB and Cache Subnet Group)"
  type        = string
  default     = "ap-southeast-1b"
}
