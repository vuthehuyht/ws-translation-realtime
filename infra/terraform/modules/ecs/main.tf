# ECS Fargate Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-cluster"
    Environment = var.environment
  }
}

# CloudWatch Log Groups for Container Logs
resource "aws_cloudwatch_log_group" "web" {
  name              = "/ecs/${var.project_name}-${var.environment}-web"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-web-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project_name}-${var.environment}-backend"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-backend-logs"
    Environment = var.environment
  }
}

# 1. Frontend Web Task Definition (Next.js 15 Standalone: 0.5 vCPU, 1 GB RAM)
resource "aws_ecs_task_definition" "web" {
  family                   = "${var.project_name}-${var.environment}-web"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.web_task_role_arn

  container_definitions = jsonencode([
    {
      name      = "web"
      image     = var.web_image
      essential = true
      portMappings = [
        {
          containerPort = 3000
          hostPort      = 3000
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "NODE_ENV", value = "production" },
        { name = "PORT", value = "3000" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.web.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "web"
        }
      }
    }
  ])

  tags = {
    Name        = "${var.project_name}-${var.environment}-web-task"
    Environment = var.environment
  }
}

# 2. Backend Task Definition (FastAPI + uvloop: 1 vCPU, 2 GB RAM, stopTimeout=120)
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-${var.environment}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.backend_task_role_arn

  container_definitions = jsonencode([
    {
      name        = "backend"
      image       = var.backend_image
      essential   = true
      stopTimeout = 120 # 120s graceful handover for WebSockets on SIGTERM
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "ENV", value = var.environment },
        { name = "AWS_DEFAULT_REGION", value = var.aws_region },
        { name = "DATABASE_URL", value = var.database_url },
        { name = "REDIS_URL", value = var.redis_url },
        { name = "S3_MEDIA_BUCKET", value = var.s3_bucket_name },
        { name = "APPSYNC_GRAPHQL_URL", value = var.appsync_graphql_url },
        { name = "DYNAMODB_TABLE_USERS", value = var.users_table_name },
        { name = "DYNAMODB_TABLE_WALLETS", value = var.wallets_table_name },
        { name = "DYNAMODB_TABLE_PAYMENTS", value = var.payment_transactions_table_name },
        { name = "DYNAMODB_TABLE_ROOMS", value = var.rooms_table_name },
        { name = "DYNAMODB_TABLE_TRANSCRIPTS", value = var.room_transcripts_table_name },
        { name = "DYNAMODB_TABLE_USAGE_LEDGER", value = var.usage_ledger_table_name }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "backend"
        }
      }
    }
  ])

  tags = {
    Name        = "${var.project_name}-${var.environment}-backend-task"
    Environment = var.environment
  }
}

# 3. ECS Service: Frontend Web
resource "aws_ecs_service" "web" {
  name            = "${var.project_name}-${var.environment}-web-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.web.arn
  desired_count   = var.web_desired_count
  launch_type     = "FARGATE"

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_web_sg_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.web_target_group_arn
    container_name   = "web"
    container_port   = 3000
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-web-service"
    Environment = var.environment
  }
}

# 4. ECS Service: Backend (API + Realtime Audio Ingest)
resource "aws_ecs_service" "backend" {
  name            = "${var.project_name}-${var.environment}-backend-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_backend_sg_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.backend_target_group_arn
    container_name   = "backend"
    container_port   = 8000
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-backend-service"
    Environment = var.environment
  }
}
