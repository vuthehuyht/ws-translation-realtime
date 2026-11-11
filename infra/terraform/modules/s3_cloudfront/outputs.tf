output "bucket_id" {
  description = "The ID of the S3 media bucket"
  value       = aws_s3_bucket.media.id
}

output "bucket_name" {
  description = "The name of the S3 media bucket"
  value       = aws_s3_bucket.media.bucket
}

output "bucket_arn" {
  description = "The ARN of the S3 media bucket"
  value       = aws_s3_bucket.media.arn
}

output "cloudfront_domain_name" {
  description = "Domain name of CloudFront distribution"
  value       = aws_cloudfront_distribution.media.domain_name
}

output "cloudfront_distribution_arn" {
  description = "ARN of CloudFront distribution"
  value       = aws_cloudfront_distribution.media.arn
}
