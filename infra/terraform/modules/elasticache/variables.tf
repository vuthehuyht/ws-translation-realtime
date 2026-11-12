variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "ws-translation"
}

variable "subnet_ids" {
  description = "List of private database subnet IDs for cache subnet group"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security groups associated with the Redis node"
  type        = list(string)
}

variable "primary_az" {
  description = "Target Availability Zone for Single-AZ node"
  type        = string
  default     = "ap-southeast-1a"
}

variable "node_type" {
  description = "ElastiCache instance node type"
  type        = string
  default     = "cache.t4g.micro"
}
