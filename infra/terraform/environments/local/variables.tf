variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "ap-southeast-1"
}

variable "aws_profile" {
  description = "AWS CLI profile name"
  type        = string
  default     = ""
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "local"
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "ws-translation"
}

variable "override_allowed_cidr" {
  description = "Override developer CIDR block. If empty, automatically queries checkip.amazonaws.com"
  type        = string
  default     = ""
}

variable "devbox_instance_type" {
  description = "EC2 instance type for DevBox running PostgreSQL 16 and Redis 7"
  type        = string
  default     = "t4g.micro"
}

variable "jwt_secret_key" {
  description = "Shared JWT HMAC secret for ephemeral guest tokens"
  type        = string
  default     = "local-dev-ephemeral-jwt-secret-key-32chars-min!!"
  sensitive   = true
}
