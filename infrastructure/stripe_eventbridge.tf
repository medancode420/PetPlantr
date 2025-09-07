# PetPlantr Production Infrastructure - Stripe + EventBridge
# Story 3.4: Stripe + EventBridge prod toggle

# Note: required_providers are defined in main.tf

# EventBridge Custom Bus for Stripe Events
resource "aws_cloudwatch_event_bus" "stripe_events" {
  name = "petplantr-stripe-events"

  tags = {
    Project     = "PetPlantr"
    Environment = "production"
    Component   = "eventbridge"
  }
}

# IAM Role for Lambda Function
resource "aws_iam_role" "stripe_webhook_processor" {
  name = "petplantr-stripe-webhook-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project     = "PetPlantr"
    Environment = "production"
  }
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "stripe_webhook_processor" {
  name = "petplantr-stripe-webhook-processor-policy"
  role = aws_iam_role.stripe_webhook_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "events:PutEvents"
        ]
        Resource = aws_cloudwatch_event_bus.stripe_events.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = "arn:aws:ssm:*:*:parameter/petplantr/*"
      }
    ]
  })
}

# Lambda Function for Stripe Webhook Processing
resource "aws_lambda_function" "stripe_webhook_processor" {
  filename         = "stripe_webhook_processor.zip"
  function_name    = "petplantr-stripe-webhook-processor"
  role            = aws_iam_role.stripe_webhook_processor.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      EVENTBRIDGE_BUS = aws_cloudwatch_event_bus.stripe_events.name
      STRIPE_SECRET_KEY = var.stripe_secret_key
    }
  }

  tags = {
    Project     = "PetPlantr"
    Environment = "production"
  }

  depends_on = [aws_iam_role_policy.stripe_webhook_processor]
}

# EventBridge Rules for Different Event Types
resource "aws_cloudwatch_event_rule" "payment_success" {
  name           = "petplantr-stripe-payment-success"
  event_bus_name = aws_cloudwatch_event_bus.stripe_events.name

  event_pattern = jsonencode({
    source      = ["stripe.webhook"]
    detail-type = ["Stripe payment_intent.succeeded"]
  })

  tags = {
    Project     = "PetPlantr"
    Environment = "production"
  }
}

resource "aws_cloudwatch_event_rule" "payment_failure" {
  name           = "petplantr-stripe-payment-failure"
  event_bus_name = aws_cloudwatch_event_bus.stripe_events.name

  event_pattern = jsonencode({
    source      = ["stripe.webhook"]
    detail-type = ["Stripe payment_intent.payment_failed"]
  })

  tags = {
    Project     = "PetPlantr"
    Environment = "production"
  }
}

resource "aws_cloudwatch_event_rule" "subscription_events" {
  name           = "petplantr-stripe-subscription-events"
  event_bus_name = aws_cloudwatch_event_bus.stripe_events.name

  event_pattern = jsonencode({
    source = ["stripe.webhook"]
    detail-type = [
      "Stripe customer.subscription.created",
      "Stripe customer.subscription.updated",
      "Stripe customer.subscription.deleted"
    ]
  })

  tags = {
    Project     = "PetPlantr"
    Environment = "production"
  }
}

# API Gateway for Webhook Endpoint
resource "aws_api_gateway_rest_api" "stripe_webhooks" {
  name        = "petplantr-stripe-webhooks"
  description = "API Gateway for Stripe webhook events"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Project     = "PetPlantr"
    Environment = "production"
  }
}

resource "aws_api_gateway_resource" "stripe" {
  rest_api_id = aws_api_gateway_rest_api.stripe_webhooks.id
  parent_id   = aws_api_gateway_rest_api.stripe_webhooks.root_resource_id
  path_part   = "stripe"
}

resource "aws_api_gateway_method" "stripe_post" {
  rest_api_id   = aws_api_gateway_rest_api.stripe_webhooks.id
  resource_id   = aws_api_gateway_resource.stripe.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "stripe_lambda" {
  rest_api_id = aws_api_gateway_rest_api.stripe_webhooks.id
  resource_id = aws_api_gateway_resource.stripe.id
  http_method = aws_api_gateway_method.stripe_post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.stripe_webhook_processor.invoke_arn
}

resource "aws_api_gateway_deployment" "stripe" {
  depends_on = [aws_api_gateway_integration.stripe_lambda]

  rest_api_id = aws_api_gateway_rest_api.stripe_webhooks.id
  stage_name  = "prod"
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.stripe_webhook_processor.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.stripe_webhooks.execution_arn}/*/*"
}

# CloudWatch Alarms for Monitoring
resource "aws_cloudwatch_metric_alarm" "webhook_errors" {
  alarm_name          = "petplantr-stripe-webhook-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Monitor Stripe webhook processing errors"

  dimensions = {
    FunctionName = aws_lambda_function.stripe_webhook_processor.function_name
  }

  tags = {
    Project     = "PetPlantr"
    Environment = "production"
  }
}

resource "aws_cloudwatch_metric_alarm" "webhook_duration" {
  alarm_name          = "petplantr-stripe-webhook-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "5000"
  alarm_description   = "Monitor Stripe webhook processing latency"

  dimensions = {
    FunctionName = aws_lambda_function.stripe_webhook_processor.function_name
  }

  tags = {
    Project     = "PetPlantr"
    Environment = "production"
  }
}

# SSM Parameters for Secrets
resource "aws_ssm_parameter" "stripe_secret_key" {
  name        = "/petplantr/production/stripe/secret-key"
  description = "Stripe production secret key"
  type        = "SecureString"
  value       = var.stripe_secret_key

  tags = {
    Project     = "PetPlantr"
    Environment = "production"
  }
}

resource "aws_ssm_parameter" "stripe_webhook_secret" {
  name        = "/petplantr/production/stripe/webhook-secret"
  description = "Stripe webhook signing secret"
  type        = "SecureString"
  value       = var.stripe_webhook_secret

  tags = {
    Project     = "PetPlantr"
    Environment = "production"
  }
}

# Outputs
output "eventbridge_bus_arn" {
  description = "ARN of the EventBridge custom bus"
  value       = aws_cloudwatch_event_bus.stripe_events.arn
}

output "lambda_function_arn" {
  description = "ARN of the Stripe webhook processor Lambda"
  value       = aws_lambda_function.stripe_webhook_processor.arn
}

output "api_gateway_url" {
  description = "URL of the API Gateway webhook endpoint"
  value       = aws_api_gateway_deployment.stripe.invoke_url
}

output "webhook_endpoint" {
  description = "Complete webhook endpoint URL"
  value       = "${aws_api_gateway_deployment.stripe.invoke_url}/stripe"
}
