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
    http = {
      source  = "hashicorp/http"
      version = "~> 3.4"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
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

# 1. Lookup AWS Default VPC and Subnets (No expensive NAT Gateway required)
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# 2. Auto-detect caller public IP for security group whitelist
data "http" "my_ip" {
  url = "https://checkip.amazonaws.com"
}

locals {
  developer_cidr = var.override_allowed_cidr != "" ? var.override_allowed_cidr : "${chomp(data.http.my_ip.response_body)}/32"
}

# 3. Standalone EC2 DevBox: PostgreSQL 16 + Redis 7 on 1 instance
module "dev_box_ec2" {
  source = "../../modules/dev_box_ec2"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = data.aws_vpc.default.id
  subnet_id           = tolist(data.aws_subnets.default.ids)[0]
  allowed_cidr_blocks = [local.developer_cidr]
  instance_type       = var.devbox_instance_type
}

# 4. S3 Media & Transcript Bucket with CloudFront CDN
module "s3_cloudfront" {
  source = "../../modules/s3_cloudfront"

  project_name = var.project_name
  environment  = var.environment
}

# 5. Amazon Cognito User Pool for Host Auth
module "cognito" {
  source = "../../modules/cognito"

  project_name = var.project_name
  environment  = var.environment
}

# 6. AWS AppSync Realtime Events WebSocket API
module "appsync" {
  source = "../../modules/appsync"

  project_name = var.project_name
  environment  = var.environment
}

# 7. IAM Developer User & Access Key for Local Machine Backend
resource "aws_iam_user" "local_dev_user" {
  name = "${var.project_name}-${var.environment}-user"

  tags = {
    Name        = "${var.project_name}-${var.environment}-user"
    Environment = var.environment
  }
}

resource "aws_iam_access_key" "local_dev_key" {
  user = aws_iam_user.local_dev_user.name
}

resource "aws_iam_user_policy" "local_dev_policy" {
  name = "${var.project_name}-${var.environment}-policy"
  user = aws_iam_user.local_dev_user.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3MediaBucketAccess"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          module.s3_cloudfront.bucket_arn,
          "${module.s3_cloudfront.bucket_arn}/*"
        ]
      },
      {
        Sid    = "CognitoAuthAccess"
        Effect = "Allow"
        Action = [
          "cognito-idp:AdminCreateUser",
          "cognito-idp:AdminInitiateAuth",
          "cognito-idp:AdminGetUser",
          "cognito-idp:AdminUpdateUserAttributes",
          "cognito-idp:InitiateAuth",
          "cognito-idp:SignUp",
          "cognito-idp:ConfirmSignUp",
          "cognito-idp:ForgotPassword",
          "cognito-idp:ConfirmForgotPassword",
          "cognito-idp:GetUser"
        ]
        Resource = [module.cognito.user_pool_arn]
      },
      {
        Sid    = "AppSyncGraphQLAccess"
        Effect = "Allow"
        Action = [
          "appsync:GraphQL"
        ]
        Resource = [
          "${module.appsync.api_arn}/*"
        ]
      },
      {
        Sid    = "RealtimeAIServicesAccess"
        Effect = "Allow"
        Action = [
          "transcribe:StartStreamTranscriptionWebSocket",
          "translate:TranslateText",
          "polly:SynthesizeSpeech",
          "bedrock:InvokeModel"
        ]
        Resource = ["*"]
      }
    ]
  })
}

# 8. Auto-render Backend .env.dev for local IDE
resource "local_file" "backend_env" {
  filename = "${path.module}/../../../../apps/backend/.env.dev"
  content = templatefile("${path.module}/templates/backend.env.tftpl", {
    aws_region            = var.aws_region
    aws_access_key_id     = aws_iam_access_key.local_dev_key.id
    aws_secret_access_key = aws_iam_access_key.local_dev_key.secret
    database_url          = module.dev_box_ec2.database_url
    redis_url             = module.dev_box_ec2.redis_url
    cognito_user_pool_id  = module.cognito.user_pool_id
    cognito_client_id     = module.cognito.user_pool_client_id
    s3_bucket_name        = module.s3_cloudfront.bucket_name
    cdn_base_url          = module.s3_cloudfront.cloudfront_domain_name
    appsync_endpoint_url  = module.appsync.graphql_url
    appsync_api_key       = module.appsync.api_key
    jwt_secret_key        = var.jwt_secret_key
  })
}

# 9. Auto-render Web Client .env.local for local frontend
resource "local_file" "web_env" {
  filename = "${path.module}/../../../../apps/web/.env.local"
  content = templatefile("${path.module}/templates/web.env.tftpl", {
    cognito_user_pool_id = module.cognito.user_pool_id
    cognito_client_id    = module.cognito.user_pool_client_id
    appsync_endpoint_url = module.appsync.graphql_url
    appsync_api_key      = module.appsync.api_key
    cdn_base_url         = module.s3_cloudfront.cloudfront_domain_name
  })
}
