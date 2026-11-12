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
  default     = "prod"
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "ws-translation"
}

variable "db_instance_class" {
  description = "Production RDS PostgreSQL instance class"
  type        = string
  default     = "db.t4g.small"
}

variable "web_desired_count" {
  description = "Desired number of ECS tasks for Web frontend service"
  type        = number
  default     = 2
}

variable "backend_desired_count" {
  description = "Desired number of ECS tasks for Backend service"
  type        = number
  default     = 2
}

variable "alert_email" {
  description = "Optional email address to subscribe to CloudWatch production alarms via SNS"
  type        = string
  default     = ""
}
