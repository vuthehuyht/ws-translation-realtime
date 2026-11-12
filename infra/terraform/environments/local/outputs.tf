output "devbox_public_ip" {
  description = "Public IP of DevBox EC2 (hosting PostgreSQL 16 & Redis 7)"
  value       = module.dev_box_ec2.public_ip
}

output "database_url" {
  description = "Async PostgreSQL connection string"
  value       = module.dev_box_ec2.database_url
  sensitive   = true
}

output "redis_url" {
  description = "Redis connection string"
  value       = module.dev_box_ec2.redis_url
  sensitive   = true
}

output "whitelisted_developer_cidr" {
  description = "Developer public IP automatically allowed in DevBox Security Group"
  value       = local.developer_cidr
}

output "s3_bucket_name" {
  description = "S3 Media bucket name"
  value       = module.s3_cloudfront.bucket_name
}

output "cloudfront_domain_name" {
  description = "CloudFront CDN domain for TTS audio chunks and assets"
  value       = module.s3_cloudfront.cloudfront_domain_name
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = module.cognito.user_pool_id
}

output "cognito_client_id" {
  description = "Cognito Web Client ID"
  value       = module.cognito.user_pool_client_id
}

output "appsync_endpoint_url" {
  description = "AppSync Realtime Subtitle Fan-out GraphQL URL"
  value       = module.appsync.graphql_url
}

output "backend_env_path" {
  description = "Path to auto-generated backend environment file"
  value       = local_file.backend_env.filename
}

output "web_env_path" {
  description = "Path to auto-generated web client environment file"
  value       = local_file.web_env.filename
}
