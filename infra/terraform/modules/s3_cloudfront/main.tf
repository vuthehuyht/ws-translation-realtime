# Random suffix for globally unique S3 bucket name
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Media & Transcripts S3 Bucket
resource "aws_s3_bucket" "media" {
  bucket        = "${var.project_name}-${var.environment}-media-${random_id.bucket_suffix.hex}"
  force_destroy = var.environment == "prod" ? false : true

  tags = {
    Name        = "${var.project_name}-${var.environment}-media"
    Environment = var.environment
  }
}

# Block all direct public access
resource "aws_s3_bucket_public_access_block" "media" {
  bucket = aws_s3_bucket.media.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Server-Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  # TTS Audio Chunks expire after 1 day (24 hours)
  rule {
    id     = "expire-tts-audio-24h"
    status = "Enabled"

    filter {
      prefix = "tts/"
    }

    expiration {
      days = 1
    }
  }

  # Compiled Transcripts (.txt, .srt, .vtt, .csv, .json) expire after 90 days
  rule {
    id     = "expire-transcripts-90d"
    status = "Enabled"

    filter {
      prefix = "transcripts/"
    }

    expiration {
      days = 90
    }
  }

  # Bedrock AI Meeting Summaries expire after 90 days
  rule {
    id     = "expire-summaries-90d"
    status = "Enabled"

    filter {
      prefix = "summaries/"
    }

    expiration {
      days = 90
    }
  }
}

# CORS Configuration for Web Audio Playback
resource "aws_s3_bucket_cors_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    max_age_seconds = 3600
  }
}

# CloudFront Origin Access Control (OAC)
resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "${var.project_name}-${var.environment}-s3-oac"
  description                       = "Origin Access Control for secure S3 media bucket read"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Distribution for global low-latency TTS audio distribution
resource "aws_cloudfront_distribution" "media" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CDN for ${var.project_name} TTS audio chunks"
  price_class         = "PriceClass_100"
  default_root_object = ""

  origin {
    domain_name              = aws_s3_bucket.media.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.media.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.media.id}"

    forwarded_values {
      query_string = false
      headers      = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400  # 24 hours
    max_ttl                = 604800 # 7 days
    compress               = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-cdn"
    Environment = var.environment
  }
}

# S3 Bucket Policy allowing CloudFront OAC read
resource "aws_s3_bucket_policy" "allow_cloudfront" {
  bucket = aws_s3_bucket.media.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipalReadOnly"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.media.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.media.arn
          }
        }
      }
    ]
  })
}
