variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "ws-translation"
}

variable "callback_urls" {
  description = "Allowed OAuth callback URLs for the Cognito web app client"
  type        = list(string)
  default     = ["http://localhost:3000/api/auth/callback"]
}

variable "logout_urls" {
  description = "Allowed OAuth sign-out URLs for the Cognito web app client"
  type        = list(string)
  default     = ["http://localhost:3000/login"]
}
