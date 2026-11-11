output "alb_sg_id" {
  description = "Security Group ID of the Application Load Balancer"
  value       = aws_security_group.alb.id
}

output "ecs_web_sg_id" {
  description = "Security Group ID of ECS Frontend Service"
  value       = aws_security_group.ecs_web.id
}

output "ecs_backend_sg_id" {
  description = "Security Group ID of ECS Backend Service"
  value       = aws_security_group.ecs_backend.id
}

output "redis_sg_id" {
  description = "Security Group ID of ElastiCache Redis"
  value       = aws_security_group.redis.id
}
