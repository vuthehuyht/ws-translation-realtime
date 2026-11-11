# Assume role policy for ECS tasks
data "aws_iam_policy_document" "ecs_tasks_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# 1. ECS Task Execution Role (Pull from ECR & write logs to CloudWatch)
resource "aws_iam_role" "ecs_execution_role" {
  name               = "${var.project_name}-${var.environment}-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json

  tags = {
    Name        = "${var.project_name}-${var.environment}-ecs-execution-role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# 2. ECS Web Task Role (Minimal frontend runtime permissions)
resource "aws_iam_role" "ecs_web_task_role" {
  name               = "${var.project_name}-${var.environment}-ecs-web-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json

  tags = {
    Name        = "${var.project_name}-${var.environment}-ecs-web-task-role"
    Environment = var.environment
  }
}

# 3. ECS Backend Task Role (Least-privilege AWS AI pipeline permissions)
resource "aws_iam_role" "ecs_backend_task_role" {
  name               = "${var.project_name}-${var.environment}-ecs-backend-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json

  tags = {
    Name        = "${var.project_name}-${var.environment}-ecs-backend-task-role"
    Environment = var.environment
  }
}

resource "aws_iam_policy" "backend_ai_and_data_policy" {
  name        = "${var.project_name}-${var.environment}-backend-ai-policy"
  description = "Permissions for FastAPI container to interact with Transcribe, Translate, Polly, Bedrock, DynamoDB, S3, and AppSync"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Amazon Transcribe Streaming (WebSocket HTTP/2)
      {
        Sid    = "AllowTranscribeStreaming"
        Effect = "Allow"
        Action = [
          "transcribe:StartStreamTranscriptionWebSocket"
        ]
        Resource = "*"
      },
      # Amazon Translate (Parallel N-Language MT)
      {
        Sid    = "AllowAmazonTranslate"
        Effect = "Allow"
        Action = [
          "translate:TranslateText"
        ]
        Resource = "*"
      },
      # Amazon Polly Neural (Demand-Driven TTS)
      {
        Sid    = "AllowAmazonPolly"
        Effect = "Allow"
        Action = [
          "polly:SynthesizeSpeech"
        ]
        Resource = "*"
      },
      # Amazon Bedrock (On-demand AI Meeting Summary via Claude 3.5 Haiku / Nova Lite)
      {
        Sid    = "AllowAmazonBedrock"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-haiku*",
          "arn:aws:bedrock:*::foundation-model/amazon.nova-lite*"
        ]
      },
      # DynamoDB: 6 Tables and GSIs CRUD
      {
        Sid    = "AllowDynamoDBCRUD"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchWriteItem",
          "dynamodb:BatchGetItem"
        ]
        Resource = var.dynamodb_table_arns
      },
      # S3: Media bucket read, write, and presigned URLs
      {
        Sid    = "AllowS3MediaOperations"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      },
      # AppSync: Publish subtitle events
      {
        Sid    = "AllowAppSyncPublish"
        Effect = "Allow"
        Action = [
          "appsync:GraphQL"
        ]
        Resource = [
          "${var.appsync_api_arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "backend_ai_attachment" {
  role       = aws_iam_role.ecs_backend_task_role.name
  policy_arn = aws_iam_policy.backend_ai_and_data_policy.arn
}
