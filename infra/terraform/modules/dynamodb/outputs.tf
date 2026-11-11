output "users_table_name" {
  description = "Name of Users DynamoDB table"
  value       = aws_dynamodb_table.users.name
}

output "users_table_arn" {
  description = "ARN of Users DynamoDB table"
  value       = aws_dynamodb_table.users.arn
}

output "wallets_table_name" {
  description = "Name of Wallets DynamoDB table"
  value       = aws_dynamodb_table.wallets.name
}

output "wallets_table_arn" {
  description = "ARN of Wallets DynamoDB table"
  value       = aws_dynamodb_table.wallets.arn
}

output "payment_transactions_table_name" {
  description = "Name of PaymentTransactions DynamoDB table"
  value       = aws_dynamodb_table.payment_transactions.name
}

output "payment_transactions_table_arn" {
  description = "ARN of PaymentTransactions DynamoDB table"
  value       = aws_dynamodb_table.payment_transactions.arn
}

output "rooms_table_name" {
  description = "Name of Rooms DynamoDB table"
  value       = aws_dynamodb_table.rooms.name
}

output "rooms_table_arn" {
  description = "ARN of Rooms DynamoDB table"
  value       = aws_dynamodb_table.rooms.arn
}

output "room_transcripts_table_name" {
  description = "Name of RoomTranscripts DynamoDB table"
  value       = aws_dynamodb_table.room_transcripts.name
}

output "room_transcripts_table_arn" {
  description = "ARN of RoomTranscripts DynamoDB table"
  value       = aws_dynamodb_table.room_transcripts.arn
}

output "usage_ledger_table_name" {
  description = "Name of UsageLedger DynamoDB table"
  value       = aws_dynamodb_table.usage_ledger.name
}

output "usage_ledger_table_arn" {
  description = "ARN of UsageLedger DynamoDB table"
  value       = aws_dynamodb_table.usage_ledger.arn
}

output "all_table_arns" {
  description = "List of all DynamoDB table and GSI ARNs for IAM policy"
  value = [
    aws_dynamodb_table.users.arn,
    "${aws_dynamodb_table.users.arn}/index/*",
    aws_dynamodb_table.wallets.arn,
    aws_dynamodb_table.payment_transactions.arn,
    "${aws_dynamodb_table.payment_transactions.arn}/index/*",
    aws_dynamodb_table.rooms.arn,
    "${aws_dynamodb_table.rooms.arn}/index/*",
    aws_dynamodb_table.room_transcripts.arn,
    aws_dynamodb_table.usage_ledger.arn,
    "${aws_dynamodb_table.usage_ledger.arn}/index/*",
  ]
}
