# 1. Lookup Latest Amazon Linux 2023 AMI for ARM64 (for t4g instance family)
data "aws_ami" "al2023_arm64" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-kernel-*-arm64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# 2. Generate Random Secure Passwords for PostgreSQL and Redis
resource "random_password" "postgres" {
  length  = 24
  special = false # Avoid URL encoding issues in connection string
}

resource "random_password" "redis" {
  length  = 24
  special = false
}

# 3. Security Group Whitelisting Developer Public IP
resource "aws_security_group" "dev_box" {
  name        = "${var.project_name}-${var.environment}-devbox-sg"
  description = "Whitelisted ingress for local dev to access PostgreSQL and Redis"
  vpc_id      = var.vpc_id

  # Ingress PostgreSQL (Port 5432)
  ingress {
    description = "PostgreSQL 16 from developer IP"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  # Ingress Redis (Port 6379)
  ingress {
    description = "Redis 7 from developer IP"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  # Optional SSH (Port 22)
  dynamic "ingress" {
    for_each = var.key_name != "" ? [1] : []
    content {
      description = "SSH access from developer IP"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = var.allowed_cidr_blocks
    }
  }

  # Egress: Full outbound access to pull Docker packages & images
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-devbox-sg"
    Environment = var.environment
  }
}

# 4. User Data Script: Setup 2GB Swap, Docker, PostgreSQL 16 & Redis 7
locals {
  user_data = <<-EOF
    #!/bin/bash
    set -euxo pipefail

    echo "=== 1. Configure 2GB Swap Space to prevent OOM on micro instance ==="
    fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    sysctl vm.swappiness=10
    echo 'vm.swappiness=10' >> /etc/sysctl.conf

    echo "=== 2. Install and Start Docker ==="
    dnf update -y
    dnf install -y docker
    systemctl enable --now docker
    usermod -aG docker ec2-user

    echo "=== 3. Prepare Persistent Data Directories ==="
    mkdir -p /opt/devbox/postgres_data
    mkdir -p /opt/devbox/redis_data
    chmod 777 /opt/devbox/postgres_data /opt/devbox/redis_data

    echo "=== 4. Launch PostgreSQL 16 Container ==="
    docker run -d \
      --name dev-postgres \
      --restart always \
      -p 5432:5432 \
      -e POSTGRES_USER=postgres \
      -e POSTGRES_PASSWORD=${random_password.postgres.result} \
      -e POSTGRES_DB=translation_db \
      -v /opt/devbox/postgres_data:/var/lib/postgresql/data \
      postgres:16-alpine

    echo "=== 5. Launch Redis 7 Container ==="
    docker run -d \
      --name dev-redis \
      --restart always \
      -p 6379:6379 \
      -v /opt/devbox/redis_data:/data \
      redis:7-alpine \
      redis-server --requirepass ${random_password.redis.result} --appendonly yes

    echo "=== DevBox initialization complete ==="
  EOF
}

# 5. Standalone EC2 Instance in Default VPC
resource "aws_instance" "dev_box" {
  ami                         = data.aws_ami.al2023_arm64.id
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [aws_security_group.dev_box.id]
  associate_public_ip_address = true
  key_name                    = var.key_name != "" ? var.key_name : null

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.volume_size_gb
    delete_on_termination = true
    encrypted             = true
  }

  user_data = local.user_data

  tags = {
    Name        = "${var.project_name}-${var.environment}-devbox"
    Environment = var.environment
    Service     = "DatabaseAndCache"
  }
}
