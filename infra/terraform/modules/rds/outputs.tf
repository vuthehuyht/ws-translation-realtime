output "instance_id" {
  description = "RDS DB instance identifier"
  value       = aws_db_instance.postgres.identifier
}

output "endpoint" {
  description = "Connection endpoint in host:port format"
  value       = aws_db_instance.postgres.endpoint
}

output "address" {
  description = "Hostname of the RDS instance"
  value       = aws_db_instance.postgres.address
}

output "port" {
  description = "Database port"
  value       = aws_db_instance.postgres.port
}

output "database_name" {
  description = "Name of the default database"
  value       = aws_db_instance.postgres.db_name
}

output "master_username" {
  description = "Master username for PostgreSQL"
  value       = aws_db_instance.postgres.username
}

output "master_password" {
  description = "Master password for PostgreSQL"
  value       = random_password.db_master.result
  sensitive   = true
}

output "database_url" {
  description = "Async SQLAlchemy asyncpg connection string"
  value       = "postgresql+asyncpg://${aws_db_instance.postgres.username}:${random_password.db_master.result}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
  sensitive   = true
}

output "security_group_id" {
  description = "Security group ID of the RDS instance"
  value       = aws_security_group.rds.id
}
