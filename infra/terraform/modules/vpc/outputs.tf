output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs for ALB"
  value       = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

output "private_compute_subnet_ids" {
  description = "List of private subnet IDs for ECS tasks (AZ-a only)"
  value       = [aws_subnet.private_compute_a.id]
}

output "private_db_subnet_ids" {
  description = "List of private database subnet IDs for ElastiCache Subnet Group"
  value       = [aws_subnet.private_db_a.id, aws_subnet.private_db_b.id]
}
