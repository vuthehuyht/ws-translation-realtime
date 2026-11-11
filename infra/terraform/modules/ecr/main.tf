# ECR Repository for Frontend Web (Next.js 15 Standalone)
resource "aws_ecr_repository" "web" {
  name                 = "${var.project_name}/web"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.project_name}-web-ecr"
    Environment = var.environment
  }
}

# ECR Repository for Backend (FastAPI + uvloop)
resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}/backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.project_name}-backend-ecr"
    Environment = var.environment
  }
}

# Shared Lifecycle Policy (Keep last N images to prevent storage bloat)
locals {
  lifecycle_policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last ${var.max_image_count} images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = var.max_image_count
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "web" {
  repository = aws_ecr_repository.web.name
  policy     = local.lifecycle_policy
}

resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name
  policy     = local.lifecycle_policy
}
