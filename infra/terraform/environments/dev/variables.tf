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
  default     = "dev"
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "ws-translation"
}

variable "db_instance_class" {
  description = "RDS PostgreSQL instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "web_desired_count" {
  description = "Desired number of ECS tasks for Web frontend service"
  type        = number
  default     = 1
}

variable "backend_desired_count" {
  description = "Desired number of ECS tasks for Backend service"
  type        = number
  default     = 1
}

variable "web_image_tag" {
  description = "Immutable ECR image tag or digest for the Web container"
  type        = string
  default     = "v0.1.0"

  validation {
    condition     = trimspace(var.web_image_tag) != "" && trimspace(var.web_image_tag) != "latest"
    error_message = "web_image_tag must be an immutable tag or digest, never 'latest'."
  }
}

variable "backend_image_tag" {
  description = "Immutable ECR image tag or digest for the Backend container"
  type        = string
  default     = "v0.1.0"

  validation {
    condition     = trimspace(var.backend_image_tag) != "" && trimspace(var.backend_image_tag) != "latest"
    error_message = "backend_image_tag must be an immutable tag or digest, never 'latest'."
  }
}

variable "acm_certificate_arn" {
  description = "Optional ACM certificate ARN to enable HTTPS:443 on the dev ALB"
  type        = string
  default     = ""
}

variable "app_domain" {
  description = "Optional dev HTTPS domain name (defaults to ALB DNS name)"
  type        = string
  default     = ""
}

variable "cors_origins" {
  description = "Explicit allowed CORS origins for dev backend"
  type        = list(string)
  default     = []
}
