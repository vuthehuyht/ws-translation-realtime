output "execution_role_arn" {
  description = "ARN of ECS Task Execution Role"
  value       = aws_iam_role.ecs_execution_role.arn
}

output "web_task_role_arn" {
  description = "ARN of ECS Web Task Role"
  value       = aws_iam_role.ecs_web_task_role.arn
}

output "backend_task_role_arn" {
  description = "ARN of ECS Backend Task Role"
  value       = aws_iam_role.ecs_backend_task_role.arn
}
