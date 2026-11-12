variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "local"
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "ws-translation"
}

variable "vpc_id" {
  description = "VPC ID where the EC2 instance will be created (typically Default VPC)"
  type        = string
}

variable "subnet_id" {
  description = "Public Subnet ID where the EC2 instance will reside"
  type        = string
}

variable "allowed_cidr_blocks" {
  description = "List of developer public IP CIDRs allowed to access PostgreSQL (5432) and Redis (6379)"
  type        = list(string)
}

variable "instance_type" {
  description = "EC2 instance type for dev box (t4g.micro with 2GB swap recommended)"
  type        = string
  default     = "t4g.micro"
}

variable "volume_size_gb" {
  description = "Root EBS gp3 volume size in GB"
  type        = number
  default     = 20
}

variable "key_name" {
  description = "Optional EC2 SSH Key Pair name"
  type        = string
  default     = ""
}
