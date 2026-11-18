variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "ws-translation"
}

variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "ap-southeast-1"
}

variable "private_subnet_ids" {
  description = "Private compute subnets for ECS tasks (AZ-a only to guarantee $0 cross-AZ transfer)"
  type        = list(string)
}

variable "ecs_web_sg_id" {
  description = "Security Group ID of ECS Web service"
  type        = string
}

variable "ecs_backend_sg_id" {
  description = "Security Group ID of ECS Backend service"
  type        = string
}

variable "web_target_group_arn" {
  description = "Target group ARN for Web frontend"
  type        = string
}

variable "backend_target_group_arn" {
  description = "Target group ARN for Backend API and WebSocket"
  type        = string
}

variable "execution_role_arn" {
  description = "Task Execution Role ARN"
  type        = string
}

variable "web_task_role_arn" {
  description = "Web Task Role ARN"
  type        = string
}

variable "backend_task_role_arn" {
  description = "Backend Task Role ARN"
  type        = string
}

variable "web_image" {
  description = "ECR image URI for frontend container"
  type        = string
}

variable "backend_image" {
  description = "ECR image URI for backend container"
  type        = string
}

variable "redis_url" {
  description = "Redis connection endpoint URL"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 media bucket"
  type        = string
}

variable "appsync_graphql_url" {
  description = "AppSync GraphQL Endpoint"
  type        = string
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID for host authentication"
  type        = string
}

variable "cognito_client_id" {
  description = "Cognito App Client ID for host authentication"
  type        = string
}

variable "cors_origins" {
  description = "Explicit allowed CORS origins for the backend API"
  type        = list(string)
}

variable "cookie_secure" {
  description = "Whether backend auth cookies require HTTPS (Secure flag)"
  type        = bool
  default     = true
}

variable "database_url_secret_arn" {
  description = "Secrets Manager ARN storing the PostgreSQL asyncpg DATABASE_URL"
  type        = string
  default     = ""
}

variable "jwt_secret_key_secret_arn" {
  description = "Secrets Manager ARN storing the JWT_SECRET_KEY"
  type        = string
  default     = ""
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
