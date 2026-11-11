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

variable "users_table_name" {
  description = "DynamoDB Users table name"
  type        = string
}

variable "wallets_table_name" {
  description = "DynamoDB Wallets table name"
  type        = string
}

variable "payment_transactions_table_name" {
  description = "DynamoDB PaymentTransactions table name"
  type        = string
}

variable "rooms_table_name" {
  description = "DynamoDB Rooms table name"
  type        = string
}

variable "room_transcripts_table_name" {
  description = "DynamoDB RoomTranscripts table name"
  type        = string
}

variable "usage_ledger_table_name" {
  description = "DynamoDB UsageLedger table name"
  type        = string
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
