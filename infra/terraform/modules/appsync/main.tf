# AppSync Realtime WebSocket API for 1,000-listener subtitle fan-out
resource "aws_appsync_graphql_api" "events" {
  name                = "${var.project_name}-${var.environment}-events"
  authentication_type = "API_KEY"

  additional_authentication_provider {
    authentication_type = "AWS_IAM"
  }

  schema = <<EOF
schema {
  query: Query
  mutation: Mutation
  subscription: Subscription
}

type Query {
  getRoomHealth(roomId: ID!): String
}

type SubtitleEvent {
  roomId: ID!
  lang: String!
  seqId: Int!
  isFinal: Boolean!
  text: String!
  timestampMs: Float!
}

type Mutation {
  publishSubtitleEvent(
    roomId: ID!
    lang: String!
    seqId: Int!
    isFinal: Boolean!
    text: String!
    timestampMs: Float!
  ): SubtitleEvent
}

type Subscription {
  onSubtitleEvent(roomId: ID!, lang: String!): SubtitleEvent
    @aws_subscribe(mutations: ["publishSubtitleEvent"])
}
EOF

  tags = {
    Name        = "${var.project_name}-${var.environment}-appsync"
    Environment = var.environment
  }
}

# Default API Key for Listeners Web Client
resource "aws_appsync_api_key" "listener_key" {
  api_id      = aws_appsync_graphql_api.events.id
  description = "Default public read key for listener subscription"
  expires     = timeadd(timestamp(), "8736h") # 364 days (AWS limit < 365 days)

  lifecycle {
    ignore_changes = [expires]
  }
}

# None DataSource for pure Pub/Sub Event Fan-out (No compute/database cost)
resource "aws_appsync_datasource" "none" {
  api_id = aws_appsync_graphql_api.events.id
  name   = "NoneSource"
  type   = "NONE"
}

# Resolver for publishSubtitleEvent mutation
resource "aws_appsync_resolver" "publish" {
  api_id      = aws_appsync_graphql_api.events.id
  type        = "Mutation"
  field       = "publishSubtitleEvent"
  data_source = aws_appsync_datasource.none.name

  request_template = <<EOF
{
  "version": "2017-02-28",
  "payload": $util.toJson($context.arguments)
}
EOF

  response_template = <<EOF
$util.toJson($context.result)
EOF
}
