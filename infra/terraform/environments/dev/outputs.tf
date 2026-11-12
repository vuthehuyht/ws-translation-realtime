output "alb_dns_name" {
  description = "Public DNS name of Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "web_app_url" {
  description = "Public URL for Next.js Web Application"
  value       = "http://${module.alb.alb_dns_name}"
}

output "backend_api_url" {
  description = "Public REST API base URL"
  value       = "http://${module.alb.alb_dns_name}/api/v1"
}

output "backend_ws_url" {
  description = "Public WebSocket Ingest base URL"
  value       = "ws://${module.alb.alb_dns_name}/ws/v1"
}

output "rds_endpoint" {
  description = "RDS PostgreSQL connection endpoint"
  value       = module.rds.endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = "${module.elasticache.redis_endpoint}:${module.elasticache.redis_port}"
}

output "cloudfront_domain" {
  description = "CloudFront CDN domain for media assets"
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
  description = "AWS AppSync Events GraphQL / WSS Endpoint"
  value       = module.appsync.graphql_url
}

output "ecr_backend_repository_url" {
  description = "ECR Repository URL for Backend Docker image"
  value       = module.ecr.backend_repository_url
}

output "ecr_web_repository_url" {
  description = "ECR Repository URL for Web Docker image"
  value       = module.ecr.web_repository_url
}
