# Multi-Environment Terraform Infrastructure

Infrastructure as Code (IaC) for **Realtime Speech-to-Speech & Speech-to-Text Translation System** deployed on AWS Singapore (`ap-southeast-1`).

---

## 1. Environments Overview

| Environment | Directory | Purpose | Architecture | Cost Profile |
| :--- | :--- | :--- | :--- | :--- |
| **`local`** | `environments/local/` | Developer machine connection for backend/web (`localhost`) | **Default VPC**: 1x EC2 `t4g.micro` (PostgreSQL 16 + Redis 7 + 2GB swap + IP whitelist), S3, Cognito, AppSync, IAM Dev Access Key. Auto-renders `.env.dev` and `.env.local`. | **~$3/month** |
| **`dev`** | `environments/dev/` | Staging / Development running 100% on AWS | **Custom Single-AZ VPC**: RDS PostgreSQL 16 (`db.t4g.micro`), ElastiCache Redis 7 (`cache.t4g.micro`), ECS Fargate (`backend` + `web`), ALB, S3, Cognito, AppSync. | **~$35-$45/month** |
| **`prod`** | `environments/prod/` | High-Availability Production running 100% on AWS | **Production-grade VPC**: RDS PostgreSQL 16 (Multi-AZ, KMS encryption, 7-day backups), ElastiCache Redis, ECS Fargate with CPU Autoscaling, ALB with AWS WAFv2 DDoS protection, S3 KMS, CloudWatch Alarms. | Pay-as-you-go |

---

## 2. Directory Structure

```text
infra/terraform/
├── environments/
│   ├── local/                     # Local Dev-Connect Environment (Default VPC + DevBox EC2)
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── templates/             # Auto-generates apps/backend/.env.dev & apps/web/.env.local
│   │   └── terraform.tfvars.example
│   │
│   ├── dev/                       # Full Development Environment on AWS
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars.example
│   │
│   └── prod/                      # High-Availability Production Environment on AWS
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── terraform.tfvars.example
│
└── modules/
    ├── dev_box_ec2/               # [NEW] 1x EC2 t4g.micro running PostgreSQL 16 & Redis 7 (Local Dev)
    ├── rds/                       # [NEW] Amazon RDS PostgreSQL 16 (Dev & Prod)
    ├── elasticache/               # ElastiCache Redis 7.1 Single-AZ node in ap-southeast-1a
    ├── waf/                       # [NEW] AWS WAFv2 WebACL Rate Limiting & OWASP Protection (Prod)
    ├── vpc/                       # Custom Single-AZ VPC in ap-southeast-1a
    ├── security/                  # Least-privilege Security Groups
    ├── ecr/                       # ECR Repositories for web & backend with 10-image lifecycle policy
    ├── s3_cloudfront/             # S3 Media Bucket (24h TTS / 90d Transcript lifecycle) + CloudFront OAC
    ├── cognito/                   # Cognito User Pool & App Client for Host Auth
    ├── appsync/                   # AppSync Events WebSocket Pub/Sub API
    ├── alb/                       # Application Load Balancer with WebSocket path-based routing
    ├── iam/                       # ECS Execution Role and Backend Task Role with AI permissions
    └── ecs/                       # ECS Fargate Cluster, Task Definitions, and Services
```

---

## 3. Quick Start Guide

### A. Deploy `local` Environment (For Localhost Development)

```bash
cd infra/terraform/environments/local

# 1. Initialize
terraform init

# 2. Review plan (auto-detects your public IP for PostgreSQL/Redis whitelist)
terraform plan

# 3. Apply infrastructure & auto-render .env files
terraform apply

# The files `apps/backend/.env.dev` and `apps/web/.env.local` will be generated automatically!
```

### B. Deploy `dev` Environment (Full AWS Staging)

```bash
cd infra/terraform/environments/dev
terraform init
terraform plan
terraform apply
```

### C. Deploy `prod` Environment (Production AWS)

```bash
cd infra/terraform/environments/prod
terraform init
terraform plan
terraform apply
```

---

## 4. Verification & Linting

```bash
# Format check all Terraform files recursively
terraform fmt -check -recursive infra/terraform

# Validate each environment
cd infra/terraform/environments/local && terraform validate
cd ../dev && terraform validate
cd ../prod && terraform validate
```
