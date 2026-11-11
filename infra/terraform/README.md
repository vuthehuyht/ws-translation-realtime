# AWS Single-AZ Terraform Infrastructure

Infrastructure as Code (IaC) for **Realtime Speech-to-Speech & Speech-to-Text Translation System** deployed on AWS Singapore (`ap-southeast-1`).

## Architecture Highlights

1. **Single-AZ Optimization (`ap-southeast-1a`)**:
   - Compute (`ECS Fargate`) and in-memory cache (`ElastiCache Redis`) reside in `ap-southeast-1a`.
   - **$0 Cross-AZ Data Transfer** when continuously reading and writing audio streams.
   - Internal Redis ring buffer latency `< 1ms`.
2. **Serverless Fan-out for 1,000 Listeners**:
   - AWS AppSync Events WebSocket Pub/Sub handles subtitle distribution without backend compute load.
   - Amazon CloudFront + S3 with Origin Access Control (OAC) distributes TTS `.mp3` audio chunks globally.
3. **High-Availability & Zero-Downtime Handover (`FR-602`)**:
   - Minimum 2 ECS Tasks running per service with Deployment Circuit Breaker & Automatic Rollback.
   - 120s Deregistration Delay on ALB Target Group and 120s `stopTimeout` on container definitions.
4. **Serverless NoSQL Persistence**:
   - 6 DynamoDB tables in `PAY_PER_REQUEST` On-Demand mode with automated 24-hour TTL on hot transcripts.

## Module Directory Structure

```text
infra/terraform/
├── main.tf                    # Root module orchestrating all infrastructure components
├── variables.tf               # Global input variables
├── outputs.tf                 # Key resource outputs (ALB DNS, ECR URLs, DynamoDB ARNs, etc.)
├── terraform.tfvars.example   # Example variables for local/dev/prod environments
└── modules/
    ├── vpc/                   # Single-AZ VPC, Subnets, IGW, NAT Gateway
    ├── security/              # Least-privilege Security Groups
    ├── ecr/                   # ECR Repositories for web & backend with 10-image lifecycle policy
    ├── dynamodb/              # 6 On-Demand DynamoDB tables + GSIs + TTL
    ├── redis/                 # ElastiCache Redis 7.1 Single-AZ node in ap-southeast-1a
    ├── s3_cloudfront/         # S3 Media Bucket (24h TTS / 90d Transcript lifecycle) + CloudFront OAC
    ├── cognito/               # Cognito User Pool & App Client for Host Auth
    ├── appsync/               # AppSync Events WebSocket GraphQL API
    ├── alb/                   # Application Load Balancer with WebSocket path-based routing
    ├── iam/                   # ECS Execution Role and Backend Task Role with AI permissions
    └── ecs/                   # ECS Fargate Cluster, Task Definitions, and Services
```

## Quick Start

### 1. Initialize Terraform
```bash
cd infra/terraform
terraform init
```

### 2. Format & Validate
```bash
terraform fmt -recursive
terraform validate
```

### 3. Plan Deployment
```bash
terraform plan -var-file="terraform.tfvars"
```

### 4. Apply
```bash
terraform apply -var-file="terraform.tfvars"
```
