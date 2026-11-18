terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile != "" ? var.aws_profile : null

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# 1. AWS KMS Customer Managed Key for Production At-Rest Encryption
resource "aws_kms_key" "prod" {
  description             = "KMS Key for ${var.project_name} Production database and storage encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-kms"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "prod" {
  name          = "alias/${var.project_name}-${var.environment}"
  target_key_id = aws_kms_key.prod.key_id
}

# 2. Custom Single-AZ VPC with Multi-AZ DB & Public Subnets
module "vpc" {
  source = "../../modules/vpc"

  project_name = var.project_name
  environment  = var.environment
}

# 3. Security Groups
module "security" {
  source = "../../modules/security"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
}

# 4. ECR Repositories with Image Scanning on Push
module "ecr" {
  source = "../../modules/ecr"

  project_name = var.project_name
  environment  = var.environment
}

# 5. Production RDS PostgreSQL 16 (Multi-AZ, KMS Encryption, 7-day Backups)
module "rds" {
  source = "../../modules/rds"

  project_name               = var.project_name
  environment                = var.environment
  vpc_id                     = module.vpc.vpc_id
  subnet_ids                 = module.vpc.private_db_subnet_ids
  ingress_security_group_ids = [module.security.ecs_backend_sg_id]
  instance_class             = var.db_instance_class
  multi_az                   = true
  deletion_protection        = true
  backup_retention_period    = 7
  kms_key_id                 = aws_kms_key.prod.arn
}

# 6. Production ElastiCache Redis 7
module "elasticache" {
  source = "../../modules/elasticache"

  project_name       = var.project_name
  environment        = var.environment
  subnet_ids         = module.vpc.private_db_subnet_ids
  security_group_ids = [module.security.redis_sg_id]
  primary_az         = "${var.aws_region}a"
  node_type          = "cache.t4g.small"
}

# 7. S3 Media Bucket + CloudFront CDN (OAC & Lifecycle)
module "s3_cloudfront" {
  source = "../../modules/s3_cloudfront"

  project_name = var.project_name
  environment  = var.environment
}

# 10. Amazon Cognito User Pool for Host Auth (after ALB/domain locals below)
locals {
  default_app_origin     = var.app_domain != "" ? "https://${var.app_domain}" : "https://${module.alb.alb_dns_name}"
  effective_cors_origins = length(var.cors_origins) > 0 ? var.cors_origins : [local.default_app_origin]
}

module "cognito" {
  source = "../../modules/cognito"

  project_name  = var.project_name
  environment   = var.environment
  callback_urls = ["${local.default_app_origin}/api/auth/callback"]
  logout_urls   = ["${local.default_app_origin}/login"]
}

# 11. AWS AppSync Events WebSocket API for Subtitle Fan-out
module "appsync" {
  source = "../../modules/appsync"

  project_name = var.project_name
  environment  = var.environment
}

# 12. Runtime Secrets stored in Secrets Manager (encrypted with Prod KMS CMK)
resource "random_password" "jwt_secret" {
  length  = 48
  special = false
}

resource "aws_secretsmanager_secret" "database_url" {
  name       = "${var.project_name}-${var.environment}-database-url"
  kms_key_id = aws_kms_key.prod.arn
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = module.rds.database_url
}

resource "aws_secretsmanager_secret" "jwt_secret_key" {
  name       = "${var.project_name}-${var.environment}-jwt-secret-key"
  kms_key_id = aws_kms_key.prod.arn
}

resource "aws_secretsmanager_secret_version" "jwt_secret_key" {
  secret_id     = aws_secretsmanager_secret.jwt_secret_key.id
  secret_string = random_password.jwt_secret.result
}

# 13. IAM Execution & Backend Task Roles
module "iam" {
  source = "../../modules/iam"

  project_name    = var.project_name
  environment     = var.environment
  s3_bucket_arn   = module.s3_cloudfront.bucket_arn
  appsync_api_arn = module.appsync.api_arn
  secret_arns = [
    aws_secretsmanager_secret.database_url.arn,
    aws_secretsmanager_secret.jwt_secret_key.arn,
  ]
  kms_key_arn = aws_kms_key.prod.arn
}

# 14. Application Load Balancer
module "alb" {
  source = "../../modules/alb"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  public_subnet_ids   = module.vpc.public_subnet_ids
  security_group_id   = module.security.alb_sg_id
  acm_certificate_arn = var.acm_certificate_arn
}

# 15. AWS WAFv2 WebACL Protection for Production ALB
module "waf" {
  source = "../../modules/waf"

  project_name        = var.project_name
  environment         = var.environment
  alb_arn             = module.alb.alb_arn
  rate_limit_per_5min = 2000
}

# 16. Production ECS Fargate Cluster & Services
module "ecs" {
  source = "../../modules/ecs"

  project_name              = var.project_name
  environment               = var.environment
  aws_region                = var.aws_region
  private_subnet_ids        = module.vpc.private_compute_subnet_ids
  ecs_web_sg_id             = module.security.ecs_web_sg_id
  ecs_backend_sg_id         = module.security.ecs_backend_sg_id
  web_target_group_arn      = module.alb.web_target_group_arn
  backend_target_group_arn  = module.alb.backend_target_group_arn
  execution_role_arn        = module.iam.execution_role_arn
  web_task_role_arn         = module.iam.web_task_role_arn
  backend_task_role_arn     = module.iam.backend_task_role_arn
  web_image                 = "${module.ecr.web_repository_url}:${var.web_image_tag}"
  backend_image             = "${module.ecr.backend_repository_url}:${var.backend_image_tag}"
  redis_url                 = "${module.elasticache.redis_url}/0"
  s3_bucket_name            = module.s3_cloudfront.bucket_name
  appsync_graphql_url       = module.appsync.graphql_url
  cognito_user_pool_id      = module.cognito.user_pool_id
  cognito_client_id         = module.cognito.user_pool_client_id
  cors_origins              = local.effective_cors_origins
  cookie_secure             = true
  database_url_secret_arn   = aws_secretsmanager_secret.database_url.arn
  jwt_secret_key_secret_arn = aws_secretsmanager_secret.jwt_secret_key.arn
  web_desired_count         = var.web_desired_count
  backend_desired_count     = var.backend_desired_count
}

# 14. ECS Backend Auto-scaling Target & CPU Tracking Policy
resource "aws_appautoscaling_target" "backend_scaling" {
  max_capacity       = 10
  min_capacity       = var.backend_desired_count
  resource_id        = "service/${var.project_name}-${var.environment}-cluster/${module.ecs.backend_service_name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "backend_cpu_scaling" {
  name               = "${var.project_name}-${var.environment}-backend-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend_scaling.resource_id
  scalable_dimension = aws_appautoscaling_target.backend_scaling.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend_scaling.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# 15. Production Monitoring, CloudWatch Alarms & SNS Alert Topic
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"

  tags = {
    Name        = "${var.project_name}-${var.environment}-alerts"
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "email_alert" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_cloudwatch_metric_alarm" "backend_cpu_high" {
  alarm_name          = "${var.project_name}-${var.environment}-backend-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "Alarm when ECS Backend CPU utilization exceeds 85% for 2 minutes"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = "${var.project_name}-${var.environment}-cluster"
    ServiceName = module.ecs.backend_service_name
  }
}
