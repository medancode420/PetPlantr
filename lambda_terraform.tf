
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

resource "aws_lambda_function" "img_thumb_512" {
  function_name = "img-thumb-512"
  runtime       = "python3.9"
  handler       = "lambda_function.lambda_handler"
  timeout       = 30

  filename         = "lambda_deploy.zip"
  source_code_hash = filebase64sha256("lambda_deploy.zip")

  environment {
    variables = {
      TARGET_SIZE = "224x224"
    }
  }

  tags = {
    Project     = "PetPlantr"
    Environment = "production"
    Component   = "image-processing"
  }
}

resource "aws_api_gateway_rest_api" "img_thumb_api" {
  name        = "img-thumb-api"
  description = "PetPlantr Image Thumbnail API"
}

resource "aws_api_gateway_resource" "resize" {
  rest_api_id = aws_api_gateway_rest_api.img_thumb_api.id
  parent_id   = aws_api_gateway_rest_api.img_thumb_api.root_resource_id
  path_part   = "resize"
}

resource "aws_api_gateway_method" "post_resize" {
  rest_api_id   = aws_api_gateway_rest_api.img_thumb_api.id
  resource_id   = aws_api_gateway_resource.resize.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_resize" {
  rest_api_id = aws_api_gateway_rest_api.img_thumb_api.id
  resource_id = aws_api_gateway_resource.resize.id
  http_method = aws_api_gateway_method.post_resize.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.img_thumb_512.invoke_arn
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.img_thumb_512.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.img_thumb_api.execution_arn}/*/*"
}

output "api_endpoint" {
  value = "${aws_api_gateway_rest_api.img_thumb_api.execution_arn}/resize"
}
