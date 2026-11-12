output "instance_id" {
  description = "ID of the DevBox EC2 instance"
  value       = aws_instance.dev_box.id
}

output "public_ip" {
  description = "Public IP address of DevBox EC2 (for PostgreSQL and Redis)"
  value       = aws_instance.dev_box.public_ip
}

output "postgres_port" {
  description = "PostgreSQL listening port"
  value       = 5432
}

output "redis_port" {
  description = "Redis listening port"
  value       = 6379
}

output "postgres_password" {
  description = "Generated master password for PostgreSQL"
  value       = random_password.postgres.result
  sensitive   = true
}

output "redis_password" {
  description = "Generated auth password for Redis"
  value       = random_password.redis.result
  sensitive   = true
}

output "database_url" {
  description = "Async SQLAlchemy PostgreSQL connection string for FastAPI backend"
  value       = "postgresql+asyncpg://postgres:${random_password.postgres.result}@${aws_instance.dev_box.public_ip}:5432/translation_db"
  sensitive   = true
}

output "redis_url" {
  description = "Redis connection string for FastAPI backend"
  value       = "redis://:${random_password.redis.result}@${aws_instance.dev_box.public_ip}:6379/0"
  sensitive   = true
}

output "security_group_id" {
  description = "ID of the DevBox Security Group"
  value       = aws_security_group.dev_box.id
}
