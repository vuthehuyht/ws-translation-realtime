# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name        = "${var.project_name}-${var.environment}-cache-subnet-group"
  description = "Subnet group for ElastiCache Redis cluster"
  subnet_ids  = var.subnet_ids

  tags = {
    Name        = "${var.project_name}-${var.environment}-cache-subnet-group"
    Environment = var.environment
  }
}

# ElastiCache Parameter Group (Redis 7.x)
resource "aws_elasticache_parameter_group" "redis7" {
  name        = "${var.project_name}-${var.environment}-redis7-params"
  family      = "redis7"
  description = "Custom parameter group for audio stream buffer and fast eviction"

  parameter {
    name  = "maxmemory-policy"
    value = "volatile-lru"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-redis7-params"
    Environment = var.environment
  }
}

# ElastiCache Cluster (Single-AZ Node in ap-southeast-1a to achieve sub-millisecond latency and $0 cross-AZ fee)
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_name}-${var.environment}-redis"
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.node_type
  num_cache_nodes      = 1
  parameter_group_name = aws_elasticache_parameter_group.redis7.name
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = var.security_group_ids
  availability_zone    = var.primary_az

  tags = {
    Name        = "${var.project_name}-${var.environment}-redis"
    Environment = var.environment
  }
}
