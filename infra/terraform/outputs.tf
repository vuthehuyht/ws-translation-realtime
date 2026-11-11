output "alb_dns_name" {
  description = "Public entrypoint DNS of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "web_ecr_repository_url" {
  description = "ECR Repository URL for Frontend container image"
  value       = module.ecr.web_repository_url
}

output "backend_ecr_repository_url" {
  description = "ECR Repository URL for Backend container image"
  value       = module.ecr.backend_repository_url
}

output "cloudfront_domain_name" {
  description = "CloudFront CDN domain for TTS audio distribution"
  value       = module.s3_cloudfront.cloudfront_domain_name
}

output "s3_media_bucket_name" {
  description = "S3 bucket for media chunks and compiled transcripts"
  value       = module.s3_cloudfront.bucket_name
}

output "redis_endpoint" {
  description = "Internal endpoint for ElastiCache Redis"
  value       = module.redis.redis_endpoint
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID for Host Auth"
  value       = module.cognito.user_pool_id
}

output "cognito_client_id" {
  description = "Cognito App Client ID"
  value       = module.cognito.user_pool_client_id
}

output "appsync_graphql_url" {
  description = "AppSync GraphQL Endpoint"
  value       = module.appsync.graphql_url
}

output "appsync_realtime_url" {
  description = "AppSync Realtime WebSocket Endpoint"
  value       = module.appsync.realtime_url
}
