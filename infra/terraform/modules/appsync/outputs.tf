output "api_id" {
  description = "The ID of the AppSync GraphQL API"
  value       = aws_appsync_graphql_api.events.id
}

output "api_arn" {
  description = "The ARN of the AppSync GraphQL API"
  value       = aws_appsync_graphql_api.events.arn
}

output "graphql_url" {
  description = "HTTP URL of the AppSync GraphQL API"
  value       = aws_appsync_graphql_api.events.uris["GRAPHQL"]
}

output "realtime_url" {
  description = "WebSocket Realtime URL of AppSync"
  value       = aws_appsync_graphql_api.events.uris["REALTIME"]
}

output "api_key" {
  description = "API Key for listener subscriptions"
  value       = aws_appsync_api_key.listener_key.key
  sensitive   = true
}
