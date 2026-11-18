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
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# 1. Single-AZ Optimized VPC
module "vpc" {
  source = "./modules/vpc"

  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  primary_az   = var.primary_az
  secondary_az = var.secondary_az
}

# 2. Least-Privilege Security Groups
module "security" {
  source = "./modules/security"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
}

# 3. Amazon ECR Repositories (Web & Backend)
module "ecr" {
  source = "./modules/ecr"

  project_name = var.project_name
  environment  = var.environment
}

# 4. DynamoDB 6 On-Demand Tables
module "dynamodb" {
  source = "./modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment
}

# 5. ElastiCache for Redis (Single-AZ Node in ap-southeast-1a)
module "elasticache" {
  source = "./modules/elasticache"

  project_name       = var.project_name
  environment        = var.environment
  subnet_ids         = module.vpc.private_db_subnet_ids
  security_group_ids = [module.security.redis_sg_id]
  primary_az         = var.primary_az
  node_type          = var.redis_node_type
}

# 6. Media S3 Bucket & CloudFront CDN
module "s3_cloudfront" {
  source = "./modules/s3_cloudfront"

  project_name = var.project_name
  environment  = var.environment
}

# 7. Amazon Cognito User Pool for Host Auth
module "cognito" {
  source = "./modules/cognito"

  project_name = var.project_name
  environment  = var.environment
}

# 8. AWS AppSync Realtime Events API
module "appsync" {
  source = "./modules/appsync"

  project_name = var.project_name
  environment  = var.environment
}

# 9. Application Load Balancer
module "alb" {
  source = "./modules/alb"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  security_group_id = module.security.alb_sg_id
}

# 10. IAM Task Execution and Least-Privilege Task Roles
module "iam" {
  source = "./modules/iam"

  project_name        = var.project_name
  environment         = var.environment
  dynamodb_table_arns = module.dynamodb.all_table_arns
  s3_bucket_arn       = module.s3_cloudfront.bucket_arn
  appsync_api_arn     = module.appsync.api_arn
  secret_arns         = [aws_secretsmanager_secret.jwt_secret_key.arn]
}

# 11. Amazon ECS Fargate Cluster & Services
locals {
  default_origin = "https://${module.alb.alb_dns_name}"
}

resource "random_password" "jwt_secret" {
  length  = 48
  special = false
}

resource "aws_secretsmanager_secret" "jwt_secret_key" {
  name = "${var.project_name}-${var.environment}-jwt-secret-key"
}

resource "aws_secretsmanager_secret_version" "jwt_secret_key" {
  secret_id     = aws_secretsmanager_secret.jwt_secret_key.id
  secret_string = random_password.jwt_secret.result
}

module "ecs" {
  source = "./modules/ecs"

  project_name             = var.project_name
  environment              = var.environment
  aws_region               = var.aws_region
  private_subnet_ids       = module.vpc.private_compute_subnet_ids
  ecs_web_sg_id            = module.security.ecs_web_sg_id
  ecs_backend_sg_id        = module.security.ecs_backend_sg_id
  web_target_group_arn     = module.alb.web_target_group_arn
  backend_target_group_arn = module.alb.backend_target_group_arn
  execution_role_arn       = module.iam.execution_role_arn
  web_task_role_arn        = module.iam.web_task_role_arn
  backend_task_role_arn    = module.iam.backend_task_role_arn

  web_image     = var.web_image != "" ? var.web_image : "${module.ecr.web_repository_url}:v0.1.0"
  backend_image = var.backend_image != "" ? var.backend_image : "${module.ecr.backend_repository_url}:v0.1.0"

  web_desired_count     = var.web_desired_count
  backend_desired_count = var.backend_desired_count

  redis_url                 = "${module.elasticache.redis_url}/0"
  s3_bucket_name            = module.s3_cloudfront.bucket_name
  appsync_graphql_url       = module.appsync.graphql_url
  cognito_user_pool_id      = module.cognito.user_pool_id
  cognito_client_id         = module.cognito.user_pool_client_id
  cors_origins              = [local.default_origin]
  cookie_secure             = false
  jwt_secret_key_secret_arn = aws_secretsmanager_secret.jwt_secret_key.arn
}
