variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "ws-translation"
}

variable "max_image_count" {
  description = "Maximum number of image tags to retain in ECR lifecycle policy"
  type        = number
  default     = 10
}
