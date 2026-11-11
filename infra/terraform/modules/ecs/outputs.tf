output "cluster_id" {
  description = "The ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "cluster_name" {
  description = "The name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "web_service_name" {
  description = "The name of the ECS Web service"
  value       = aws_ecs_service.web.name
}

output "backend_service_name" {
  description = "The name of the ECS Backend service"
  value       = aws_ecs_service.backend.name
}
