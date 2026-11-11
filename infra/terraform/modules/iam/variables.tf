variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "ws-translation"
}

variable "dynamodb_table_arns" {
  description = "List of DynamoDB table ARNs allowed for backend CRUD operations"
  type        = list(string)
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 media and transcript bucket"
  type        = string
}

variable "appsync_api_arn" {
  description = "ARN of the AppSync GraphQL API"
  type        = string
}
