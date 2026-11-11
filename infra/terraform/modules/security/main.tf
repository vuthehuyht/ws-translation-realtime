# ALB Security Group
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "Allows inbound HTTP/HTTPS traffic to ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP Ingress"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS Ingress"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-alb-sg"
    Environment = var.environment
  }
}

# ECS Frontend (Web) Security Group
resource "aws_security_group" "ecs_web" {
  name        = "${var.project_name}-${var.environment}-ecs-web-sg"
  description = "Allows inbound traffic from ALB to Next.js container on port 3000"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Inbound from ALB"
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Allow all outbound traffic for external API and CDN"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-ecs-web-sg"
    Environment = var.environment
  }
}

# ECS Backend Security Group
resource "aws_security_group" "ecs_backend" {
  name        = "${var.project_name}-${var.environment}-ecs-backend-sg"
  description = "Allows inbound traffic from ALB to FastAPI container on port 8000"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Inbound from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Allow all outbound traffic for AWS AI services and internet egress"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-ecs-backend-sg"
    Environment = var.environment
  }
}

# ElastiCache Redis Security Group (Least-privilege: Only accepts from ECS Backend)
resource "aws_security_group" "redis" {
  name        = "${var.project_name}-${var.environment}-redis-sg"
  description = "Allows inbound Redis connection on port 6379 strictly from ECS Backend tasks"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Redis from Backend Tasks"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_backend.id]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-redis-sg"
    Environment = var.environment
  }
}
