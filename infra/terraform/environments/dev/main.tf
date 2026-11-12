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

# 1. Custom Single-AZ VPC in ap-southeast-1a (+ minimal secondary AZ-b subnets for ALB)
module "vpc" {
  source = "../../modules/vpc"

  project_name = var.project_name
  environment  = var.environment
}

# 2. Security Groups with strict chaining (ALB -> ECS -> RDS & Redis)
module "security" {
  source = "../../modules/security"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
}

# 3. Private ECR Repositories for Docker images
module "ecr" {
  source = "../../modules/ecr"

  project_name = var.project_name
  environment  = var.environment
}

# 4. Amazon RDS PostgreSQL 16 (Single-AZ db.t4g.micro in private DB subnet)
module "rds" {
  source = "../../modules/rds"

  project_name               = var.project_name
  environment                = var.environment
  vpc_id                     = module.vpc.vpc_id
  subnet_ids                 = module.vpc.private_db_subnet_ids
  ingress_security_group_ids = [module.security.ecs_backend_sg_id]
  instance_class             = var.db_instance_class
  multi_az                   = false
  deletion_protection        = false
  backup_retention_period    = 1
}

# 5. ElastiCache for Redis 7 (Single-AZ cache.t4g.micro in ap-southeast-1a)
module "elasticache" {
  source = "../../modules/elasticache"

  project_name       = var.project_name
  environment        = var.environment
  subnet_ids         = module.vpc.private_db_subnet_ids
  security_group_ids = [module.security.redis_sg_id]
  primary_az         = "${var.aws_region}a"
  node_type          = "cache.t4g.micro"
}

# 6. S3 Media & Transcript Bucket + CloudFront CDN (OAC & 24h/90d lifecycles)
module "s3_cloudfront" {
  source = "../../modules/s3_cloudfront"

  project_name = var.project_name
  environment  = var.environment
}

# 7. Amazon Cognito User Pool for Host Authentication
module "cognito" {
  source = "../../modules/cognito"

  project_name = var.project_name
  environment  = var.environment
}

# 8. AWS AppSync Events WebSocket API for Realtime Subtitle Fan-out
module "appsync" {
  source = "../../modules/appsync"

  project_name = var.project_name
  environment  = var.environment
}

# 9. IAM Execution & Backend Task Roles (Transcribe, Translate, Polly, Bedrock, S3, AppSync)
module "iam" {
  source = "../../modules/iam"

  project_name    = var.project_name
  environment     = var.environment
  s3_bucket_arn   = module.s3_cloudfront.bucket_arn
  appsync_api_arn = module.appsync.api_arn
}

# 10. Application Load Balancer (Path Routing: /api/v1 & /ws/v1 -> Backend, /* -> Web)
module "alb" {
  source = "../../modules/alb"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  security_group_id = module.security.alb_sg_id
}

# 11. ECS Fargate Cluster & Services (FastAPI Backend + Next.js Standalone Frontend)
module "ecs" {
  source = "../../modules/ecs"

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
  web_image                = "${module.ecr.web_repository_url}:latest"
  backend_image            = "${module.ecr.backend_repository_url}:latest"
  database_url             = module.rds.database_url
  redis_url                = "${module.elasticache.redis_url}/0"
  s3_bucket_name           = module.s3_cloudfront.bucket_name
  appsync_graphql_url      = module.appsync.graphql_url
  web_desired_count        = var.web_desired_count
  backend_desired_count    = var.backend_desired_count
}
