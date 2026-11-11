output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "web_target_group_arn" {
  description = "ARN of Frontend Web target group"
  value       = aws_lb_target_group.web.arn
}

output "backend_target_group_arn" {
  description = "ARN of Backend target group"
  value       = aws_lb_target_group.backend.arn
}
