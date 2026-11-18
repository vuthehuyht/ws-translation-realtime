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

# ElastiCache Replication Group (Single-AZ 1-node Redis 7.1 with TLS in-transit & at-rest encryption)
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id        = "${var.project_name}-${var.environment}-redis"
  description                 = "Single-AZ Redis 7.1 cache with TLS transit encryption"
  engine                      = "redis"
  engine_version              = "7.1"
  node_type                   = var.node_type
  num_cache_clusters          = 1
  automatic_failover_enabled  = false
  parameter_group_name        = aws_elasticache_parameter_group.redis7.name
  port                        = 6379
  subnet_group_name           = aws_elasticache_subnet_group.main.name
  security_group_ids          = var.security_group_ids
  preferred_cache_cluster_azs = [var.primary_az]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-redis"
    Environment = var.environment
  }
}
