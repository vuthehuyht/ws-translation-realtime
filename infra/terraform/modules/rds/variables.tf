variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "ws-translation"
}

variable "vpc_id" {
  description = "VPC ID where RDS will be deployed"
  type        = string
}

variable "subnet_ids" {
  description = "List of private DB subnet IDs across multiple AZs"
  type        = list(string)
}

variable "ingress_security_group_ids" {
  description = "Security groups allowed to connect to PostgreSQL (e.g. ECS Backend SG)"
  type        = list(string)
}

variable "instance_class" {
  description = "RDS instance class (db.t4g.micro for dev, db.t4g.small/medium for prod)"
  type        = string
  default     = "db.t4g.micro"
}

variable "engine_version" {
  description = "PostgreSQL major.minor engine version"
  type        = string
  default     = "16.9"
}

variable "database_name" {
  description = "Initial PostgreSQL database name"
  type        = string
  default     = "translation_db"
}

variable "master_username" {
  description = "Master username for PostgreSQL"
  type        = string
  default     = "dbadmin"
}

variable "allocated_storage" {
  description = "Initial allocated storage in GB (gp3)"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum storage autoscaling limit in GB"
  type        = number
  default     = 100
}

variable "multi_az" {
  description = "Enable Multi-AZ high availability deployment"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Protect database from accidental deletion"
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "Automated backup retention days (0 to 35)"
  type        = number
  default     = 1
}

variable "kms_key_id" {
  description = "Optional KMS Key ARN for EBS storage encryption (uses default aws/rds key if null)"
  type        = string
  default     = null
}
