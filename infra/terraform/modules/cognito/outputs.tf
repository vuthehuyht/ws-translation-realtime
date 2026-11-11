output "user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.hosts.id
}

output "user_pool_arn" {
  description = "ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.hosts.arn
}

output "user_pool_endpoint" {
  description = "Endpoint of the Cognito User Pool"
  value       = aws_cognito_user_pool.hosts.endpoint
}

output "user_pool_client_id" {
  description = "Client ID of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.web_client.id
}
