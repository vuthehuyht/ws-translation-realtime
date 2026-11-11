# VPC Definition
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpc"
    Environment = var.environment
  }
}

# Internet Gateway for Public Traffic
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-${var.environment}-igw"
    Environment = var.environment
  }
}

# Public Subnets (AZ-a and AZ-b required by AWS ALB specification)
resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, 0) # 10.0.0.0/20
  availability_zone       = var.primary_az
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-public-a"
    Environment = var.environment
    Type        = "Public"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, 1) # 10.0.16.0/20
  availability_zone       = var.secondary_az
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-public-b"
    Environment = var.environment
    Type        = "Public"
  }
}

# Single-AZ Private Compute Subnet (AZ-a only to guarantee 0 cross-AZ data transfer fee)
resource "aws_subnet" "private_compute_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, 2) # 10.0.32.0/20
  availability_zone = var.primary_az

  tags = {
    Name        = "${var.project_name}-${var.environment}-private-compute-a"
    Environment = var.environment
    Type        = "Private-Compute"
  }
}

# Private Database Subnets (AZ-a primary + AZ-b standby to fulfill ElastiCache Subnet Group requirement)
resource "aws_subnet" "private_db_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, 4) # 10.0.64.0/20
  availability_zone = var.primary_az

  tags = {
    Name        = "${var.project_name}-${var.environment}-private-db-a"
    Environment = var.environment
    Type        = "Private-Database"
  }
}

resource "aws_subnet" "private_db_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, 5) # 10.0.80.0/20
  availability_zone = var.secondary_az

  tags = {
    Name        = "${var.project_name}-${var.environment}-private-db-b"
    Environment = var.environment
    Type        = "Private-Database"
  }
}

# Elastic IP for Single NAT Gateway in AZ-a
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name        = "${var.project_name}-${var.environment}-nat-eip"
    Environment = var.environment
  }
}

# NAT Gateway (Single-AZ in Public Subnet A for private tasks internet egress)
resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_a.id

  tags = {
    Name        = "${var.project_name}-${var.environment}-nat-gw"
    Environment = var.environment
  }

  depends_on = [aws_internet_gateway.main]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-public-rt"
    Environment = var.environment
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-private-rt"
    Environment = var.environment
  }
}

# Route Table Associations
resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private_compute_a" {
  subnet_id      = aws_subnet.private_compute_a.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_db_a" {
  subnet_id      = aws_subnet.private_db_a.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_db_b" {
  subnet_id      = aws_subnet.private_db_b.id
  route_table_id = aws_route_table.private.id
}
