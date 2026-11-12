variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "ws-translation"
}

variable "alb_arn" {
  description = "Application Load Balancer ARN to associate with the WAF WebACL"
  type        = string
}

variable "rate_limit_per_5min" {
  description = "Rate limit per 5 minutes per IP address"
  type        = number
  default     = 2000
}
