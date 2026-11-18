output "redis_endpoint" {
  description = "The primary endpoint hostname of the Redis node"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "redis_port" {
  description = "The port on which Redis is listening"
  value       = aws_elasticache_replication_group.redis.port
}

output "redis_url" {
  description = "Complete TLS-enabled Redis connection URL"
  value       = "rediss://${aws_elasticache_replication_group.redis.primary_endpoint_address}:${aws_elasticache_replication_group.redis.port}"
}
