output "web_repository_url" {
  description = "The URL of the Web ECR repository"
  value       = aws_ecr_repository.web.repository_url
}

output "web_repository_arn" {
  description = "The ARN of the Web ECR repository"
  value       = aws_ecr_repository.web.arn
}

output "backend_repository_url" {
  description = "The URL of the Backend ECR repository"
  value       = aws_ecr_repository.backend.repository_url
}

output "backend_repository_arn" {
  description = "The ARN of the Backend ECR repository"
  value       = aws_ecr_repository.backend.arn
}
