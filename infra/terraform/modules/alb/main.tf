# Single Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.security_group_id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "prod" ? true : false

  tags = {
    Name        = "${var.project_name}-${var.environment}-alb"
    Environment = var.environment
  }
}

# Target Group: Frontend Web (Next.js 15 Standalone)
resource "aws_lb_target_group" "web" {
  name        = "${var.project_name}-${var.environment}-tg-web"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/login"
    protocol            = "HTTP"
    matcher             = "200-302"
    interval            = 20
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-tg-web"
    Environment = var.environment
  }
}

# Target Group: Backend (FastAPI + WebSocket Audio Ingest)
resource "aws_lb_target_group" "backend" {
  name        = "${var.project_name}-${var.environment}-tg-backend"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  # 120s Deregistration Delay gives the container 2 minutes to complete speaking turns and send HANDOVER signals
  deregistration_delay = 120

  health_check {
    path                = "/api/v1/health"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-tg-backend"
    Environment = var.environment
  }
}

# HTTP Listener on port 80 (Default action: route to frontend web)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

# Path Routing Rule: Forward /api/* and /ws/* to Backend FastAPI Target Group
resource "aws_lb_listener_rule" "backend_api_and_ws" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/ws/*"]
    }
  }
}
