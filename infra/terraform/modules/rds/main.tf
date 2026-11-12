# 1. DB Subnet Group (Private Database Subnets)
resource "aws_db_subnet_group" "postgres" {
  name        = "${var.project_name}-${var.environment}-pg-subnet-group"
  description = "Private database subnets for PostgreSQL"
  subnet_ids  = var.subnet_ids

  tags = {
    Name        = "${var.project_name}-${var.environment}-pg-subnet-group"
    Environment = var.environment
  }
}

# 2. Random Secure Password for Master User
resource "random_password" "db_master" {
  length  = 24
  special = false # Avoid special character parsing issues in asyncpg URI
}

# 3. Security Group for RDS PostgreSQL
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "Access to RDS PostgreSQL 16 from Backend services"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from ECS backend tasks"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.ingress_security_group_ids
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-rds-sg"
    Environment = var.environment
  }
}

# 4. Custom Parameter Group for PostgreSQL 16
resource "aws_db_parameter_group" "postgres16" {
  name        = "${var.project_name}-${var.environment}-pg16-params"
  family      = "postgres16"
  description = "Custom parameter group for PostgreSQL 16"

  parameter {
    name  = "client_encoding"
    value = "UTF8"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-pg16-params"
    Environment = var.environment
  }
}

# 5. RDS PostgreSQL 16 Instance
resource "aws_db_instance" "postgres" {
  identifier = "${var.project_name}-${var.environment}-db"

  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = var.kms_key_id

  db_name  = var.database_name
  username = var.master_username
  password = random_password.db_master.result
  port     = 5432

  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.postgres16.name

  publicly_accessible = false
  multi_az            = var.multi_az
  deletion_protection = var.deletion_protection

  backup_retention_period   = var.backup_retention_period
  skip_final_snapshot       = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "${var.project_name}-${var.environment}-db-final-snapshot" : null

  auto_minor_version_upgrade = true
  copy_tags_to_snapshot      = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-db"
    Environment = var.environment
  }
}
