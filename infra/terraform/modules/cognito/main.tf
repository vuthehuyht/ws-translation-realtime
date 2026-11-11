# Cognito User Pool for Host Authentication
resource "aws_cognito_user_pool" "hosts" {
  name = "${var.project_name}-${var.environment}-hosts"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  # Standard Password Policy matching frontend PasswordMeter
  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject        = "Mã xác thực tài khoản Host - WS Translation"
    email_message        = "Mã xác thực của bạn là {####}. Mã có hiệu lực trong vòng 15 phút."
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = true
    required            = true
  }

  schema {
    name                = "name"
    attribute_data_type = "String"
    mutable             = true
    required            = false
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-hosts-pool"
    Environment = var.environment
  }
}

# Cognito User Pool Client for Web Application
resource "aws_cognito_user_pool_client" "web_client" {
  name         = "${var.project_name}-${var.environment}-web-client"
  user_pool_id = aws_cognito_user_pool.hosts.id

  generate_secret               = false
  prevent_user_existence_errors = "ENABLED"
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
  ]
  supported_identity_providers         = ["COGNITO"]
  callback_urls                        = ["http://localhost:3000/api/auth/callback"]
  logout_urls                          = ["http://localhost:3000/login"]
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  allowed_oauth_flows_user_pool_client = true

  access_token_validity  = 60 # minutes
  id_token_validity      = 60 # minutes
  refresh_token_validity = 30 # days

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}
