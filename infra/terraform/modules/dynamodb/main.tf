# 1. Users Table (Synced from Cognito post-confirmation)
resource "aws_dynamodb_table" "users" {
  name         = "${var.project_name}-${var.environment}-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "userId"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  global_secondary_index {
    name            = "GSI-Email"
    hash_key        = "email"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-users"
    Environment = var.environment
  }
}

# 2. Wallets Table (1-1 with Host)
resource "aws_dynamodb_table" "wallets" {
  name         = "${var.project_name}-${var.environment}-wallets"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "hostId"

  attribute {
    name = "hostId"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-wallets"
    Environment = var.environment
  }
}

# 3. PaymentTransactions Table (Idempotent top-ups and refunds)
resource "aws_dynamodb_table" "payment_transactions" {
  name         = "${var.project_name}-${var.environment}-payment-transactions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "transactionId"

  attribute {
    name = "transactionId"
    type = "S"
  }

  attribute {
    name = "hostId"
    type = "S"
  }

  attribute {
    name = "createdAt"
    type = "N"
  }

  global_secondary_index {
    name            = "GSI-HostPayments"
    hash_key        = "hostId"
    range_key       = "createdAt"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-payment-transactions"
    Environment = var.environment
  }
}

# 4. Rooms Table (Session metadata and billing state)
resource "aws_dynamodb_table" "rooms" {
  name         = "${var.project_name}-${var.environment}-rooms"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "roomId"

  attribute {
    name = "roomId"
    type = "S"
  }

  attribute {
    name = "hostId"
    type = "S"
  }

  attribute {
    name = "createdAt"
    type = "N"
  }

  attribute {
    name = "roomCode"
    type = "S"
  }

  global_secondary_index {
    name            = "GSI-HostRooms"
    hash_key        = "hostId"
    range_key       = "createdAt"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "GSI-RoomCode"
    hash_key        = "roomCode"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-rooms"
    Environment = var.environment
  }
}

# 5. RoomTranscripts Table (Hot segments with 24-hour TTL)
resource "aws_dynamodb_table" "room_transcripts" {
  name         = "${var.project_name}-${var.environment}-room-transcripts"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "roomId"
  range_key    = "seqStart"

  attribute {
    name = "roomId"
    type = "S"
  }

  attribute {
    name = "seqStart"
    type = "N"
  }

  ttl {
    attribute_name = "expiresAt"
    enabled        = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-room-transcripts"
    Environment = var.environment
  }
}

# 6. UsageLedger Table (10-second micro-billing ledger)
resource "aws_dynamodb_table" "usage_ledger" {
  name         = "${var.project_name}-${var.environment}-usage-ledger"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "roomId"
  range_key    = "windowTimestamp"

  attribute {
    name = "roomId"
    type = "S"
  }

  attribute {
    name = "windowTimestamp"
    type = "N"
  }

  attribute {
    name = "hostId"
    type = "S"
  }

  global_secondary_index {
    name            = "GSI-HostLedger"
    hash_key        = "hostId"
    range_key       = "windowTimestamp"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-usage-ledger"
    Environment = var.environment
  }
}
