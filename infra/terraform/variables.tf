variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "ap-southeast-1"
}

variable "environment" {
  description = "Deployment environment name (e.g. dev, staging, prod)"
  type        = string
  default     = "dev"
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
  description = "Primary Availability Zone for compute and cache (Single-AZ optimization)"
  type        = string
  default     = "ap-southeast-1a"
}

variable "secondary_az" {
  description = "Secondary Availability Zone for ALB multi-AZ compliance"
  type        = string
  default     = "ap-southeast-1b"
}

variable "redis_node_type" {
  description = "Instance type for ElastiCache Redis"
  type        = string
  default     = "cache.t4g.micro"
}

variable "web_image" {
  description = "ECR image URI for Frontend container"
  type        = string
  default     = "" # If empty, defaults to repository URL:latest
}

variable "backend_image" {
  description = "ECR image URI for Backend container"
  type        = string
  default     = "" # If empty, defaults to repository URL:latest
}

variable "web_desired_count" {
  description = "Desired number of tasks for Web service (defaults to 0 for initial bootstrap before ECR push)"
  type        = number
  default     = 0
}

variable "backend_desired_count" {
  description = "Desired number of tasks for Backend service (defaults to 0 for initial bootstrap before ECR push)"
  type        = number
  default     = 0
}
